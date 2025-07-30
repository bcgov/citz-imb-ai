from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from app.shared.models.neo4j import neo4j

explicit_search_mcp = FastMCP(name="ExplicitSearchAgent")


@explicit_search_mcp.tool(
    name="explicit_search",
    description="""Perform a read-only cypher query against the Neo4j graph database and return relevant results.
    This is good for questions that involve counting, getting specific sections of acts, or answering questionsn about data relationships.""",
)
def search(cypher: str) -> dict:
    f"""
    Args:
        cypher (str): The cypher query to perform against the Neo4j graph database.
    Returns:
        result: The result of the cypher query execution.
    """
    # Initialize the Neo4j graph database connection
    kg = neo4j()
    # Normalize the query for checking
    normalized_query = cypher.lower().strip()

    # Remove comments and whitespace for more thorough checking
    import re

    # Remove single-line comments
    normalized_query = re.sub(r"//.*", "", normalized_query)
    # Remove multi-line comments
    normalized_query = re.sub(r"/\*.*?\*/", "", normalized_query, flags=re.DOTALL)
    # Remove extra whitespace
    normalized_query = " ".join(normalized_query.split())

    # Check for mutation keywords
    mutation_keywords = [
        "create",
        "add",
        "update",
        "set",
        "merge",
        "delete",
        "remove",
        "insert",
        "replace",
        "drop",
        "detach",
        "foreach",
        "call",
    ]

    if any(keyword in normalized_query for keyword in mutation_keywords):
        raise ToolError(
            "The cypher query contains words that indicate adding or updating data. "
            "This tool is only for searching and retrieving data."
        )

    # Additional safety: only allow queries that start with read operations
    read_operations = ["match", "return", "with", "unwind", "optional", "where"]
    first_word = normalized_query.split()[0] if normalized_query.split() else ""

    if first_word not in read_operations:
        raise ToolError(
            "Query must start with a read operation (MATCH, RETURN, WITH, UNWIND, OPTIONAL, WHERE). "
            "This tool is only for searching and retrieving data."
        )
    # Execute the cypher query
    results = kg.query(cypher)
    # Tool return type must be a dictionary or None
    return {"result": results}
