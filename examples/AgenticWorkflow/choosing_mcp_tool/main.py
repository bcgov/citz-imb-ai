# from McpServer import McpServer
from AzureQuery import AzureQuery
from Neo4jRetrieval import Neo4jRetrieval
import os
import json


# Neo4j Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "admin"
NEO4J_PASSWORD = "admin"

# Azure Configuration
endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
key = os.getenv("AZURE_AI_KEY", "")

azure = AzureQuery(endpoint, key)


def explicit_search(query: str) -> str:
    """Use a cypher query to search for information in a Neo4j database.
    Args:
        question (str): The question to search for.
    Returns:
        str: Return value from Neo4j database.
    """
    neo4j_worker = Neo4jRetrieval(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    results = neo4j_worker.run_query(query)
    neo4j_worker.close()
    return results


def semantic_search(question: str) -> str:
    """Use a vector similarity search to find relevant information in a Neo4j database.
    Args:
        question (str): The question to search for.
    Returns:
        str: A summarized response based on the search results.
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings

    neo4j_worker = Neo4jRetrieval(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
        OPTIONAL MATCH (node)-[:REFERENCES]->(refNode)
        RETURN score, 
              node.ActId AS ActId,  
              node.RegId as Regulations, 
              node.sectionId AS sectionId, 
              node.sectionName AS sectionName, 
              node.url AS url,
              node.type AS type,
              node.text AS text,
        collect({refSectionId: refNode.sectionId, refSectionName: refNode.sectionName, refActId: refNode.ActId, refText: refNode.text}) AS references
        ORDER BY score DESC
    """
    vector_index = "Acts_Updatedchunks"
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    """Search for similar nodes using the Neo4j vector index"""
    query_embedding = embeddings.embed_query(question)
    similar = neo4j_worker.run_query(
        vector_search_query,
        params={
            "question": query_embedding,
            "index_name": vector_index,
            "top_k": 10,
        },
    )

    neo4j_worker.close()

    return similar


tools = [
    {
        "type": "function",
        "function": {
            "name": "explicit_search",
            "description": "Use a cypher query to search for information in a Neo4j database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The cypher query to execute",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Use a vector similarity search to find relevant information in a Neo4j database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question used to to create embeddings for a vector similarity search",
                    }
                },
                "required": ["question"],
            },
        },
    },
]


def get_database_schema():
    """Get the database schema dynamically from Neo4j."""
    neo4j_worker = Neo4jRetrieval(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Get node labels
    labels_query = "CALL db.labels()"
    labels = neo4j_worker.run_query(labels_query)

    # Get relationship types
    relationships_query = "CALL db.relationshipTypes()"
    relationships = neo4j_worker.run_query(relationships_query)

    # Get property keys
    properties_query = "CALL db.propertyKeys()"
    properties = neo4j_worker.run_query(properties_query)

    neo4j_worker.close()

    schema_info = f"""
      Node Labels: {labels}
      Relationship Types: {relationships}
      Property Keys: {properties}
      
      Use these when constructing Cypher queries.
      """

    return schema_info


def chat_loop(initial_question: str):
    # mcp = McpServer()
    # mcp.run()  # Start the MCP server
    # tools = mcp.tools  # Ensure tools are set
    # print(tools)
    try:
        # Supply with database schema first
        schema = get_database_schema()
        azure.set_database_schema(schema)
        # Continue with the conversation
        response = azure.call_agent_with_history(initial_question, tools=tools)
        finish_reason = response.get("finish_reason")
        while finish_reason != "stop":
            if finish_reason == "tool_calls":
                tool_calls = response.get("message").get("tool_calls")
                print(response)
                for tool_call in tool_calls:
                    tool_call_id = tool_call.get("id")  # Get the tool call ID
                    tool_name = tool_call.get("function").get("name")
                    arguments_str = tool_call.get("function").get("arguments")

                    # Parse the JSON string to get a Python object
                    try:
                        arguments = json.loads(arguments_str)
                        print(f"Calling tool: {tool_name} with arguments: {arguments}")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing arguments: {e}")
                        continue
                    if tool_name == "explicit_search":
                        result = explicit_search(arguments.get("query"))
                    elif tool_name == "semantic_search":
                        result = semantic_search(arguments.get("question"))

                    print(f"Tool {tool_name} returned: {result}")
                    # Add the tool response with the correct tool_call_id
                    azure.add_tool_response(tool_call_id, result)

                # Continue the conversation without adding a new user message
                response = azure.call_agent_with_history("", tools=tools, role="user")
                finish_reason = response.get("finish_reason")
            else:
                print("Unexpected finish reason:", finish_reason)
                break
        response_text = response.get("message").get("content", "").strip()
        azure.clear_history()  # Clear history after the conversation
        return response_text
        # print("Final response:", response_text)
    except Exception as e:
        print("An error occurred:", str(e))
        raise e


if __name__ == "__main__":
    questions = [
        "How much notice is required to terminate a tenancy in BC?",
        "Which section of the Motor Vehicle Act contains rules for speed limits?",
        "How many instances of the word 'interprovincial' are there in BC laws?",
        "How many Acts have information about indigenous peoples?",
        "Which Acts and Regulations contain information on natural resources?",
    ]
    for question in questions:
        print(f"Question: {question}")
        answer = chat_loop(question)
        print(f"Answer: {answer}\n")
