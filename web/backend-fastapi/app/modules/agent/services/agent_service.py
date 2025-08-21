import os
import json
from fastapi import HTTPException, Response
from fastapi.logger import logger
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ..agents import agent_registry
from app.shared.models import neo4j
from app.shared.models.azure import AzureAI
from ..models.agent_model import AgentRequest, AgentResponse, DatabaseSchema


class AgentService:
    def __init__(self):
        self.keycloak_endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
        self.azure_key = os.getenv("AZURE_AI_KEY", "")
        self.max_iterations = 10
    
    def get_database_schema(self, labels: list[str] = []) -> DatabaseSchema:
        """Get the database schema dynamically from Neo4j."""
        neo4j_worker = neo4j.neo4j()
        
        # Get comprehensive schema information
        schema_query = """
        CALL apoc.meta.schema()
        YIELD value
        RETURN value
        """
        
        schema = neo4j_worker.query(schema_query)
        
        # Filter the schema to only include desired node labels and relationship types
        if len(labels) > 0:
            schema_obj = schema[0].get("value", {})
            # Only keep nodes with specified labels
            filtered_nodes = {
                label: properties
                for label, properties in schema_obj.items()
                if label in labels
            }
            schema = filtered_nodes
        
        # Format the schema information
        schema_info = f"""
        COMPREHENSIVE DATABASE SCHEMA:
        {schema}
        
        This schema shows:
        - Node labels with their properties and types
        - Relationship types and their directions
        - Property constraints and indexes
        - Cardinality information
        
        Please note that the field document_title actually contains the title of the document.
        Therefore, if I wanted information about a specific document, such as the Motor Vehicle Act, I would search in the document_title field.
        Use this information to construct accurate Cypher queries.
        """
        
        return DatabaseSchema(schema_info=schema_info, labels=labels)
    
    def get_initial_context(self, schema_info: str) -> str:
        """Set database schema information as a system message."""
        schema_message = f"""
        You are an AI assistant that helps users answer questions about Laws in British Columbia.
        You must utilize the provided list of tools to build enough context to answer the user's question.
        Keep your responses concise and relevant to the user's question.

        For explicit searches with cypher queries, this is the database schema information you need to know:
        {schema_info}
        Utilize this schema to construct accurate Cypher queries when needed.
        Always specify the node label that you want to search on, as this schema may not contain all labels in the database.

        Tools may be used more than once within a single conversation.
        You can use the tools to search for information, but you cannot modify the database.
        """
        return schema_message
    
    async def process_agent_chat(self, request: AgentRequest) -> AgentResponse:
        """Process agent chat request"""
        if request is None:
            raise HTTPException(status_code=400, detail="No request body provided")
        
        if not isinstance(request, AgentRequest):
            raise HTTPException(
                status_code=400, 
                detail="Input should be a valid AgentRequest object"
            )
        
        initial_question = request.prompt
        
        # Azure Configuration
        azure = AzureAI(self.keycloak_endpoint, self.azure_key)
        
        try:
            # Get combined MCP from agent registry
            combined_mcp = agent_registry.get_combined_mcp()
            # Establish MCP client connection
            client = Client(combined_mcp)
            async with client:
                raw_tools = await client.list_tools()
                # Convert tools to a format compatible with Azure
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                    for tool in raw_tools
                ]
                
                # Supply with database schema first
                schema = self.get_database_schema(["v3"])
                azure.add_system_message(self.get_initial_context(schema.schema_info))
                
                # Continue with the conversation
                response = azure.call_agent_with_history(initial_question, tools=tools)
                
                finish_reason = response.get("finish_reason")
                current_iteration = 0
                
                # Process the response until we reach a stopping condition
                while finish_reason != "stop" and current_iteration < self.max_iterations:
                    if finish_reason == "tool_calls":
                        tool_calls = response.get("message").get("tool_calls")
                        for tool_call in tool_calls:
                            tool_call_id = tool_call.get("id")  # Get the tool call ID
                            tool_name = tool_call.get("function").get("name")
                            arguments_str = tool_call.get("function").get("arguments")
                            
                            # Parse the JSON string to get a Python object
                            try:
                                arguments = json.loads(arguments_str)
                                logger.info(
                                    f"Calling tool: {tool_name} with arguments: {arguments}",
                                )
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Error parsing arguments: {e}",
                                )
                                continue
                            
                            # Handle tool execution with error handling
                            try:
                                result = await client.call_tool(tool_name, arguments)
                                logger.info(f"Tool {tool_name} returned: {result}")
                                # Add the successful tool response
                                azure.add_tool_response(tool_call_id, result)
                            except ToolError as tool_error:
                                error_message = (
                                    f"Tool error in {tool_name}: {str(tool_error)}"
                                )
                                logger.error(error_message)
                                # Pass the error back to the agent so it can adjust
                                azure.add_tool_response(
                                    tool_call_id, {"error": error_message}
                                )
                            except Exception as e:
                                error_message = f"Unexpected error in {tool_name}: {str(e)}"
                                logger.error(error_message)
                                # Pass the error back to the agent
                                azure.add_tool_response(
                                    tool_call_id, {"error": error_message}
                                )
                        
                        # Continue the conversation without adding a new user message
                        response = azure.call_agent_with_history(
                            "", tools=tools, role="user"
                        )
                        finish_reason = response.get("finish_reason")
                        current_iteration += 1
                    elif finish_reason == "length":
                        logger.warning(
                            "Input length exceeded the limit. Stopping further processing."
                        )
                        break
                    else:
                        logger.warning("Unexpected finish reason:", finish_reason)
                        break
                
                response_text = response.get("message").get("content", "").strip()
                # TODO: Filter out tool calls before returning?
                return AgentResponse(response=response_text, history=azure.history)
        
        except Exception as e:
            logger.error("An error occurred during agent processing:", exc_info=True)
            raise e
