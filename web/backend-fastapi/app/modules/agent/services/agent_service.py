import os
import json
from fastapi import HTTPException, Response
from fastapi.logger import logger
from fastmcp import Client
from fastmcp.exceptions import ToolError
from datetime import datetime, timezone

from ..agents import agent_registry
from app.shared.models import neo4j
from app.shared.models.azure import AzureAI
from ..models.agent_model import AgentRequest, AgentResponse, DatabaseSchema
from app.shared.utils.user_utils import UserInfo
from app.shared.models.postgres import get_pg_connection


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

    def build_user_context(self, user: dict) -> dict:
        user_summary = (user["summary"] or "").strip()
        user_preferences = user.get("preferences", {})
        return {
            "role": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": (
                f"""Here is some info about the user's past chats: 
              {user_summary if user_summary
              else "No user summary provided."}
              Here are the user's preferences: 
              {json.dumps(user_preferences, indent=2) if user_preferences else "No user preferences provided."}
              
              You must use this information to tailor your responses to the user unless asked to do otherwise.
              Make sure to follow the user's preferences closely in every response.
              If the user asks about their preferences, you can refer to the preferences provided.
              If the user asks about their past chats, you can refer to the summary provided.
              If the user requests that you do something that goes against their preferences, follow their instructions.
          """
            ),
        }

    async def process_agent_chat(
        self, request: AgentRequest, user: UserInfo
    ) -> AgentResponse:
        """Process agent chat request"""
        if request is None:
            raise HTTPException(status_code=400, detail="No request body provided")

        if not isinstance(request, AgentRequest):
            raise HTTPException(
                status_code=400, detail="Input should be a valid AgentRequest object"
            )

        # Azure Configuration
        azure = AzureAI(self.keycloak_endpoint, self.azure_key)

        with get_pg_connection() as conn:
            with conn.cursor() as db:
                db.execute(
                    f"""
                    SELECT * 
                    FROM "user" 
                    WHERE id = '{user.id}'
                    """
                )
                my_user = db.fetchone()
                if my_user is None:
                    # Don't error here, we just can't provide user-specific context
                    logger.warning(f"User {user.id} not found in database")

                initial_question = request.prompt
                chat_id = request.chat_id
                # If no chat_id is provided, we must insert a new chat entry
                # Chat ID is generated in the database
                if chat_id is None:
                    timestamp = datetime.now(timezone.utc).isoformat()
                    # Generate a short title for the chat based on the initial question
                    title_response = azure.call_agent_external_history(
                        [
                            {
                                "role": "system",
                                "content": "Generate a concise title (max 5 words) for the user's chat based on their initial question. The title should be descriptive and capture the essence of the question.",
                            },
                            {
                                "role": "user",
                                "content": initial_question,
                            },
                        ]
                    )
                    chat_title = (
                        title_response.get("message", {}).get("content", "").strip()
                    )
                    db.execute(
                        """
                        INSERT INTO chat (user_id, created_at, updated_at, title)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *
                        """,
                        (user.id, timestamp, timestamp, chat_title),
                    )
                    chat_record = db.fetchone()
                    if chat_record is None:
                        raise HTTPException(
                            status_code=500, detail="Failed to create new chat"
                        )
                else:
                    # Get the existing chat entry
                    db.execute(
                        f"""
                        SELECT * 
                        FROM chat 
                        WHERE id = '{chat_id}' AND user_id = '{user.id}'
                        """
                    )
                    chat_record = db.fetchone()
                    if chat_record is None:
                        raise HTTPException(
                            status_code=404, detail="Requested chat not found"
                        )
                    # Does this user even have access to this chat?
                    # User id coming from postgres has hyphens, user.id does not
                    plain_user_id = str(chat_record["user_id"]).replace("-", "")
                    if plain_user_id != user.id:
                        raise HTTPException(
                            status_code=403,
                            detail="This chat does not belong to requesting user",
                        )

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

                        # Build the chat chain.
                        # It's composed of:
                        # - the user's summary and preferences (if any),
                        # - the system message with database schema,
                        # - the previous chat history (if any),
                        # - the user's current question.
                        chat_chain = []
                        chat_chain.append(self.build_user_context(my_user))

                        # Supply with database schema
                        schema = self.get_database_schema(["v3"])
                        chat_chain.append(
                            {
                                "role": "system",
                                "content": self.get_initial_context(schema.schema_info),
                            }
                        )

                        # Add previous chat history if available
                        if chat_record and chat_record.get("chat_chain"):
                            previous_history = chat_record.get("chat_chain", [])
                            chat_chain.extend(previous_history)

                        # Finally, add the user's current question
                        chat_chain.append(
                            {
                                "role": "user",
                                "content": initial_question,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )

                        # Continue with the conversation
                        response = azure.call_agent_external_history(
                            chat_chain, tools=tools
                        )

                        finish_reason = response.get("finish_reason")
                        current_iteration = 0
                        while (
                            finish_reason != "stop"
                            and current_iteration < self.max_iterations
                        ):
                            if finish_reason == "tool_calls":
                                tool_calls = response.get("message").get("tool_calls")
                                message_content = response.get("message", {}).get(
                                    "content", ""
                                )
                                chat_chain.append(
                                    {
                                        "role": "assistant",
                                        "content": message_content,
                                        "tool_calls": tool_calls,
                                    }
                                )
                                for tool_call in tool_calls:
                                    tool_call_id = tool_call.get("id")
                                    tool_name = tool_call.get("function").get("name")
                                    arguments_str = tool_call.get("function").get(
                                        "arguments"
                                    )

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
                                        result = await client.call_tool(
                                            tool_name, arguments
                                        )
                                        logger.info(
                                            f"Tool {tool_name} returned: {result}"
                                        )
                                        # Add the successful tool response
                                        if not isinstance(result, str):
                                            result = str(result)
                                        chat_chain.append(
                                            {
                                                "role": "tool",
                                                "tool_call_id": tool_call_id,
                                                "content": result,
                                            }
                                        )
                                    except ToolError as tool_error:
                                        error_message = f"Tool error in {tool_name}: {str(tool_error)}"
                                        logger.error(error_message)
                                        # Needs to be in chat_chain so agent can adjust
                                        chat_chain.append(
                                            {
                                                "role": "tool",
                                                "tool_call_id": tool_call_id,
                                                "content": f"Error: {error_message}",
                                            }
                                        )
                                    except Exception as e:
                                        error_message = (
                                            f"Unexpected error in {tool_name}: {str(e)}"
                                        )
                                        logger.error(error_message)
                                        # Add error to chat_chain
                                        chat_chain.append(
                                            {
                                                "role": "tool",
                                                "tool_call_id": tool_call_id,
                                                "content": f"Error: {error_message}",
                                            }
                                        )

                                # Continue the conversation without adding a new user message
                                response = azure.call_agent_external_history(
                                    chat_chain, tools=tools, role="user"
                                )
                                finish_reason = response.get("finish_reason")
                                current_iteration += 1
                            elif finish_reason == "length":
                                logger.warning(
                                    "Input length exceeded the limit. Stopping further processing."
                                )
                                break
                            else:
                                logger.warning(
                                    "Unexpected finish reason:", finish_reason
                                )
                                break

                        response_text = (
                            response.get("message").get("content", "").strip()
                        )
                        if response_text:
                            chat_chain.append(
                                {
                                    "role": "assistant",
                                    "content": response_text,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                        # Update the chat entry in the database with the new chat chain
                        # Filter out any tool calls and system items from the chat history before saving
                        filtered_chat_chain = [
                            item
                            for item in chat_chain
                            if item["role"] in ["user", "assistant"]
                            and len(item.get("content") or "") > 0
                        ]
                        db.execute(
                            """
                            UPDATE chat
                            SET chat_chain = %s, updated_at = %s
                            WHERE id = %s
                            """,
                            (
                                json.dumps(filtered_chat_chain),
                                datetime.now(timezone.utc).isoformat(),
                                chat_record["id"],
                            ),
                        )

                        # Returning the full chat chain for now
                        return AgentResponse(
                            response=response_text,
                            history=chat_chain,
                            chat_id=chat_record["id"],
                            chat_title=chat_record.get("title", "Untitled Chat"),
                        )

                except Exception as e:
                    logger.error(
                        "An error occurred during agent processing:", exc_info=True
                    )
                    raise e
