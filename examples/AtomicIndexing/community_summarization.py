# Which communities do we have at each level of community depth?

from collections import defaultdict
from neo4j_functions import neo4j
from langchain.text_splitter import SentenceTransformersTokenTextSplitter

# from langchain_huggingface import HuggingFaceEmbeddings
import boto3
from botocore.config import Config
import os
import json
import concurrent.futures

token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=50, tokens_per_chunk=250
)
# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

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
    If the context is insufficient to create a response, respond with "No text content."

    Original text:
    {insert_text}
    """
    return prompt_base


FILE_PATH = "./examples/AtomicIndexing/community_summaries.jsonl"
# Get existing community summarizations from file
if os.path.exists(FILE_PATH):
    with open(FILE_PATH, "r") as f:
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
    community_depth = len(communities)
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
        if node["document_title"] is not None:
            documents_included.add(node["document_title"])
        if node["text"] is not None:
            text += node["text"] + "\n"

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
    with open(FILE_PATH, "a") as f:
        f.write(json.dumps(summary_json) + "\n")

    print(f"Community {community_number} summarized and saved.")
