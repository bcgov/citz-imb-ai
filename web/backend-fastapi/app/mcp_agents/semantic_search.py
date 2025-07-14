from fastmcp import FastMCP

semantic_search_mcp = FastMCP(name="SemanticSearchAgent")


@semantic_search_mcp.tool
def search(query: str) -> dict:
    """
    Performs a cosine similarity search against a graph database and returns relevant results.
    Args:
        query (str): The user's question to perform the cosine similarity search with.
    Returns:
        list: A list that contains the top relevant documents based on the query.
    """
    print(f"Performing semantic search for: {query}")
    # Actual semantic search logic would go here
    return {"results": [f"doc1 for {query}", f"doc2 for {query}"]}
