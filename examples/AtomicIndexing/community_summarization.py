from collections import defaultdict
from neo4j_functions import neo4j
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import boto3
from botocore.config import Config
import os
import json
import concurrent.futures

token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=50, tokens_per_chunk=250
)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Default retry mode is legacy otherwise
config = Config(retries={"max_attempts": 3, "mode": "standard"})
bedrock_runtime = session.client(
    "bedrock-runtime", region_name="us-east-1", config=config
)


# Standard kwargs for claude
def get_claude_kwargs(prompt):
    kwargs = {
        "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
            }
        ),
    }
    return kwargs


# Usual wrapper function for bedrock call
def get_agent_response(prompt):
    kwargs = get_claude_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get("body").read())
    return response_body["content"][0]["text"]


def create_prompt(insert_text):
    prompt_base = f"""
    Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness.
    Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects.
    Rely strictly on the provided text, without including external information.
    Format the summary in paragraph form for easy understanding.
    Do not include any other text.
    Do not include an introduction stating that this is a summary.
    Use markdown to format your response.
    Even if the context is insufficient to create a proper summary, try your best to summarize what's there.

    Original text:
    {insert_text}
    """
    return prompt_base


COMMUNITY_JSON_FILE_PATH = "./examples/AtomicIndexing/community_summaries.jsonl"
COMMUNITY_EMBEDDING_FILE_PATH = "./examples/AtomicIndexing/community_embeddings.jsonl"


def build_summaries():
    """
    Build summaries for communities in the database.
    This function retrieves communities from the database, processes their text content,
    and generates summaries using a language model, saving the result to file.
    """
    # Get existing community summarizations from file
    if os.path.exists(COMMUNITY_JSON_FILE_PATH):
        with open(COMMUNITY_JSON_FILE_PATH, "r") as f:
            print("File exists, loading existing summaries.")
            lines = f.readlines()
            existing_summaries = {
                json.loads(line)["community_number"]: json.loads(line)
                for line in lines
                if line.strip()
            }
    else:
        print("File does not exist, creating a new one.")
        existing_summaries = {}

    result = neo4j.query(
        """
    MATCH (n:v3) WHERE n.intermediateCommunities IS NOT NULL RETURN DISTINCT n.intermediateCommunities as communities
    """
    )

    communities_by_tier = defaultdict(set)

    for row in result:
        communities = row["communities"]
        for i, community_number in enumerate(communities):
            communities_by_tier[i].add(community_number)

    # For each community in the final tier (6)
    final_communities = communities_by_tier[len(communities_by_tier) - 1]
    for community_number in final_communities:
        # If this community is already accounted for in the map, we don't need to summarize again
        if community_number in existing_summaries:
            print(f"Community {community_number} already summarized.")
            continue
        print(f"Summarizing community {community_number}")
        # Get all nodes from this community
        nodes = neo4j.query(
            """
              MATCH (n)
              WHERE n.intermediateCommunities IS NOT NULL 
              AND n.intermediateCommunities[size(n.intermediateCommunities) - 1] = $num
              RETURN elementId(n) as id, n.document_title as document_title, n.text as text
            """,
            {"num": community_number},
        )

        # Concatenate the text of all nodes
        text = ""
        documents_included = set()
        for node in nodes:
            if node.get("document_title") is not None:
                documents_included.add(node["document_title"])
            if node.get("text") is not None:
                text += node["text"] + "\n"
            if node.get("rows") is not None:
                text += str(node["rows"]) + "\n"
            if node.get("term") is not None and node.get("definition") is not None:
                text += f"{node['term']}: {node['definition']}\n"

        chunks = token_splitter.split_text(text)

        # Combine these chunks into the maximum applicable size
        text_groups = []
        current_group = []
        for i, chunk in enumerate(chunks):
            if i != 0 and i % 15 == 0:
                text_groups.append(current_group)
                current_group = []
            current_group.append(chunk)
        # append the final group
        if len(current_group) > 0:
            text_groups.append(current_group)

        # For each text group, combine the chunks and summarize
        summaries = []

        # Use ThreadPoolExecutor to process text_groups in parallel
        def process_group(group):
            combined = " ".join(group)
            prompt = create_prompt(combined)
            return get_agent_response(prompt)

        print("Creating initial summaries")
        with concurrent.futures.ThreadPoolExecutor(4) as executor:
            # Submit tasks for each group
            futures = [executor.submit(process_group, group) for group in text_groups]

            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                summaries.append(future.result())

        # Until the it has been condensed to a single summary, combine them.
        while len(summaries) > 1:
            print(f"Summaries remaining: {len(summaries)}")
            new_summaries = []
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor(4) as executor:
                # Prepare tasks for parallel execution
                future_to_summary = {
                    executor.submit(
                        lambda pair: get_agent_response(
                            create_prompt(pair[0] + "\n" + pair[1])
                        ),
                        (summaries[i], summaries[i + 1]),
                    ): (i, i + 1)
                    for i in range(0, len(summaries) - 1, 2)
                }

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_summary):
                    new_summaries.append(future.result())

            # Handle the last summary if the number of summaries is odd
            if len(summaries) % 2 != 0:
                new_summaries.append(summaries[-1])

            summaries = new_summaries

        # Should only be a single summary now
        final_summary = summaries[0] if len(summaries) > 0 else "No text content."

        # Create json object
        summary_json = {
            "community_number": community_number,
            "summary": final_summary,
            "documents_included": list(documents_included),
        }
        # Write community summaries to file
        with open(COMMUNITY_JSON_FILE_PATH, "a") as f:
            f.write(json.dumps(summary_json) + "\n")

        print(f"Community {community_number} summarized and saved.")


def create_embeddings():
    """
    Create embeddings for community summaries and save them to a file.
    This function loads community summaries from a file, generates embeddings using a language model,
    and saves the results to a new file.
    """
    # Load the community summaries from the file
    if os.path.exists(COMMUNITY_JSON_FILE_PATH):
        with open(COMMUNITY_JSON_FILE_PATH, "r") as f:
            lines = f.readlines()
            community_summaries = [json.loads(line) for line in lines if line.strip()]
    else:
        raise Exception("community_summaries.json does not exist. Exiting.")

    # Chunk summaries into 256 token pieces
    chunked_summaries = []

    def chunk_and_embed(community):
        # Split the text into chunks
        chunks = token_splitter.split_text(community["summary"])

        for i, chunk in enumerate(chunks):
            # Create embedding for the chunk
            summary_embedding = embeddings.embed_query(chunk)
            # Parameters for the node
            params = {
                "community_number": community["community_number"],
                "documents_included": community["documents_included"],
                "chunk_summary": chunk,
                "chunk_embedding": summary_embedding,
                "chunk_index": i,
            }
            if i == 0:
                params["summary"] = community["summary"]
            chunked_summaries.append(params)

    # Create embeddings for all the summaries
    # Use ThreadPoolExecutor to parallelize embedding creation
    print("Creating embeddings for community summaries")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Process summaries in parallel and collect results
        list(executor.map(chunk_and_embed, community_summaries))
    # Save these new summaries to the same file
    with open(COMMUNITY_EMBEDDING_FILE_PATH, "w") as f:
        for item in chunked_summaries:
            f.write(json.dumps(item) + "\n")
    print("Embeddings created and saved to file.")


def create_community_nodes():
    """
    Create community nodes in the Neo4j database using the community summaries.
    This function loads community summaries from a file and inserts them into the database.
    """
    # Get existing community summarizations from file
    if os.path.exists(COMMUNITY_EMBEDDING_FILE_PATH):
        with open(COMMUNITY_EMBEDDING_FILE_PATH, "r") as f:
            lines = f.readlines()
            community_summaries = [json.loads(line) for line in lines if line.strip()]
    else:
        raise Exception("community_summaries.json does not exist. Exiting.")

    print("Sending summaries to Neo4j")
    # Create a new nodes for the communities
    result = neo4j.query(
        f"""
      UNWIND $rows AS row
      CALL (row) {{
          CREATE (n:Community_v3 {{
            community_number: row.community_number, 
            summary: row.summary, 
            documents_included: row.documents_included, 
            chunk_embedding: row.chunk_embedding, 
            chunk_index: row.chunk_index,
            chunk_summary: row.chunk_summary
          }})
          RETURN n.community_number as community_number
      }} IN CONCURRENT TRANSACTIONS OF 5000 ROWS
      ON ERROR CONTINUE
      REPORT STATUS AS s
      WITH s WHERE s.errorMessage IS NOT NULL
      RETURN s
      """,
        {"rows": community_summaries},
    )
    print("Node creation errors:", result)
    print("Community nodes created.")


def connect_community_chunks():
    """
    Connect community chunks in the Neo4j database.
    This function retrieves community nodes from the database and creates relationships
    between them based on their chunk indices.
    """
    # Get all Community_v3 nodes
    result = neo4j.query(
        """
        MATCH (n:Community_v3)
        RETURN elementId(n) AS id, n.community_number AS community_number, n.chunk_index AS chunk_index
        """
    )
    # Create a mapping of community_number to node. Each key is the community number. Each value is a list of nodes
    community_nodes = defaultdict(list)
    for row in result:
        community_number = row["community_number"]
        node_id = row["id"]
        chunk_index = row["chunk_index"]
        community_nodes[community_number].append(
            {
                "id": node_id,
                "chunk_index": chunk_index,
            }
        )
    # For each list in the community nodes, sort the community nodes by chunk_index
    for community_number, nodes in community_nodes.items():
        if len(nodes) > 1:
            # Sort the nodes by chunk_index
            sorted_nodes = sorted(nodes, key=lambda x: x["chunk_index"])
            # For each node, create a relationship to the next node
            for i in range(len(sorted_nodes) - 1):
                current_node = sorted_nodes[i]
                next_node = sorted_nodes[i + 1]
                neo4j.query(
                    """
                      MATCH (a:Community_v3), (b:Community_v3)
                      WHERE elementId(a) = $current_id AND elementId(b) = $next_id
                      MERGE (a)-[:NEXT]->(b)
                      RETURN a, b
                    """,
                    {
                        "current_id": current_node["id"],
                        "next_id": next_node["id"],
                    },
                )


def connect_communities_to_nodes():
    """
    Connect communities to their corresponding nodes in the Neo4j database.
    This function retrieves community nodes and their corresponding nodes from the database
    and creates relationships between them.
    """
    print("Connecting communities to nodes")
    # Get distinct community ids from Community_v3 nodes
    result = neo4j.query(
        """
      MATCH (n:Community_v3)
      RETURN COLLECT(DISTINCT n.community_number) AS community_numbers
      """
    )
    community_numbers = result[0]["community_numbers"]
    print(f"Getting node elementIds for {len(community_numbers)} communities")
    # For each community, get all the node IDs that belong to it
    for community_number in community_numbers:
        nodes = neo4j.query(
            """
        MATCH (n:v3)
        WHERE n.intermediateCommunities IS NOT NULL 
        AND n.intermediateCommunities[size(n.intermediateCommunities) - 1] = $num
        RETURN collect(elementId(n)) as node_ids
        """,
            {"num": community_number},
        )
        # Attach these nodes to the community node with the matching ID
        node_ids = nodes[0]["node_ids"]
        print(f"Connecting {len(node_ids)} nodes to community {community_number}")
        neo4j.query(
            """
        MATCH (n:Community_v3 {community_number: $num})
        MATCH (m:v3)
        WHERE elementId(m) IN $node_ids
        MERGE (n)-[:COMMUNITY]-(m)
        RETURN n, m
        """,
            {"num": community_number, "node_ids": node_ids},
        )
        print(f"Connected {len(node_ids)} nodes to community {community_number}")
    print("Community connections created.")


# Run functions as needed to summarize, create embeddings, insert nodes, and connect them
# build_summaries()
# create_embeddings()
# create_community_nodes()
# connect_community_chunks()
# connect_communities_to_nodes()
