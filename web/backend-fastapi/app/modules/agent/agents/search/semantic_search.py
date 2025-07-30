from fastmcp import FastMCP
from app.shared.models.rag import get_full_rag
from app.shared.models.neo4j import neo4j
from app.shared.models.rag_states import get_state_map

semantic_search_mcp = FastMCP(name="SemanticSearchAgent")
states = get_state_map()


@semantic_search_mcp.tool(
    name="semantic_search",
    description=f"""
    Performs a cosine similarity search against a graph database and returns relevant results.
    Valid options for the state_key are {[key for key in states.keys()]}.
    This is good for questions where you want to find documents with text that is similar to the user's question.""",
)
def search(query: str, state_key: str) -> dict:
    f"""
    Args:
        query (str): The user's question to perform the cosine similarity search with.
        state_key (str): The key to identify the state in the RAG system.
    Returns:
        top_k: A list that contains the top relevant documents based on the query.
    """
    print(f"Performing semantic search for: {query}")

    # Get State based on key
    state = states.get(state_key).get("state", None)
    if state is None:
        raise ValueError(
            f"Invalid state key: {state_key}. Valid options are {list(states.keys())}."
        )
    # Run RAG retrieval
    rag = get_full_rag()
    top_k = rag.retrieve(
        query,
        neo4j(),
        state,
    )
    re_ranked_results = rag.re_rank_reference(
        top_k,
        query,
    )
    # Tool return type must be a dictionary or None
    return {"top_k": re_ranked_results}
