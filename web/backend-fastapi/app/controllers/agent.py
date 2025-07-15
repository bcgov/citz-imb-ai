from typing import List
from fastapi import APIRouter, Body, Request, Response
from pydantic import BaseModel
from fastmcp import Client
from fastmcp.exceptions import ToolError
from ..mcp_agents import agents_mcp
from ..models import neo4j
from ..models.azure import AzureAI
import os
import json

router = APIRouter()


class AgentHistory(BaseModel):
    prompt: str
    response: str


class AgentRequest(BaseModel):
    prompt: str
    # chatHistory: List[AgentHistory]


def get_database_schema(labels: list[str] = []):
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
    return schema_info


def get_initial_context(schema_info):
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


@router.post("/test/")
async def agentic_chat(request: AgentRequest = None):
    if request is None:
        return Response(
            content="No request body provided",
            status_code=400,
        )

    if not isinstance(request, AgentRequest):
        return Response(
            content="Input should be a valid AgentRequest object",
            status_code=400,
        )

    initial_question = request.prompt

    # Azure Configuration
    endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
    key = os.getenv("AZURE_AI_KEY", "")
    azure = AzureAI(endpoint, key)

    max_iterations = 10

    try:
        client = Client(agents_mcp)
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
            schema = get_database_schema(["v3"])
            azure.add_system_message(get_initial_context(schema))

            # Continue with the conversation
            response = azure.call_agent_with_history(initial_question, tools=tools)

            finish_reason = response.get("finish_reason")
            current_iteration = 0
            while finish_reason != "stop" and current_iteration < max_iterations:
                if finish_reason == "tool_calls":
                    tool_calls = response.get("message").get("tool_calls")
                    for tool_call in tool_calls:
                        tool_call_id = tool_call.get("id")  # Get the tool call ID
                        tool_name = tool_call.get("function").get("name")
                        arguments_str = tool_call.get("function").get("arguments")

                        # Parse the JSON string to get a Python object
                        try:
                            arguments = json.loads(arguments_str)
                            print(
                                f"Calling tool: {tool_name} with arguments: {arguments}",
                                flush=True,
                            )
                        except json.JSONDecodeError as e:
                            print(
                                f"Error parsing arguments: {e}",
                                level="error",
                                flush=True,
                            )
                            continue
                        result = await client.call_tool(tool_name, arguments)
                        print(f"Tool {tool_name} returned: {result}", flush=True)
                        # Add the tool response with the correct tool_call_id
                        azure.add_tool_response(tool_call_id, result)

                    # Continue the conversation without adding a new user message
                    response = azure.call_agent_with_history(
                        "", tools=tools, role="user"
                    )
                    finish_reason = response.get("finish_reason")
                    current_iteration += 1
                elif finish_reason == "length":
                    print("Input length exceeded the limit.", flush=True)
                    break
                else:
                    print("Unexpected finish reason:", finish_reason, flush=True)
                    break
            response_text = response.get("message").get("content", "").strip()
            return {"response": response_text, "history": azure.history}
            # print("Final response:", response_text)
    except ToolError as e:
        print("Tool error occurred:", str(e))
        return Response(
            content=f"Tool error: {str(e)}",
            status_code=500,
        )
    except Exception as e:
        print("An error occurred:", str(e))
        raise e
