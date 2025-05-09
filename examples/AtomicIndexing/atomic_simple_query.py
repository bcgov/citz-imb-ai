###
# Included this script so that I could test the indexing directly.
# This query works against the text_embedding property found on atomically-indexed nodes, if created.
# Initial feedback from use: semantic search context too small for accurate results from Neo4j.
###

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.graphs import Neo4jGraph
import os
import json
import boto3
from neo4j_functions import neo4j

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def create_prompt(query: str, context_str: str) -> str:
    """
    Generate a response using the given context.
    """
    messages = f"""
            You are a helpful and knowledgeable assistant. Use the following information to answer the user's question accurately and concisely. Do not provide information that is not supported by the given context or chat history.

            - Use the context to form your answer.
            - Laws and Acts can be used interchangeably.
            - If the answer is not found in the context, state that you don't know.
            - Do not attempt to fabricate an answer.

            Context: 
            {context_str}

            Question: 
            {query}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
        """
    return messages


#### Adjust your question here ####
question = "How much notice do I need to give to end my rental lease in BC?"
# question = "Do I need to wear a seatbelt in BC?"

query_embeddings = embeddings.embed_query(question)

# This vector query grabs a lot of connected nodes, including:
# Any connected references
# Any nodes contained within (subsections, paragraphs, etc.)
# The node's parent
# The node's siblings
# The previous and next nodes created by the chunking process.
vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) 
        YIELD node, score
        OPTIONAL MATCH (node)-[:REFERENCES]->(refNode)
        OPTIONAL MATCH (node)-[:CONTAINS]->(containedNode)
        OPTIONAL MATCH (parent)-[:CONTAINS]->(node) // Find the parent of the node
        OPTIONAL MATCH (parent)-[:CONTAINS]->(siblingNode) 
        OPTIONAL MATCH (previousChunk)-[:NEXT*]->(node)
        OPTIONAL MATCH (node)-[:NEXT*]->(nextChunk)
        WHERE node <> siblingNode // Exclude the node itself from its siblings
        RETURN 
            score, 
            node.text AS text,
            parent.text as parentText,
            collect(DISTINCT {refText: refNode.text}) AS references,
            collect(DISTINCT {containedText: containedNode.text}) AS containedNodes,
            collect(DISTINCT {siblingText: siblingNode.text}) AS siblings,
            collect(DISTINCT {connectedText: previousChunk.text}) + collect(DISTINCT {connectedText: nextChunk.text}) AS connectedNodes
        ORDER BY score DESC
        """

NEO4J_VECTOR_INDEX = "content_embedding_v3"
similar = neo4j.query(
    vector_search_query,
    params={
        "question": query_embeddings,
        "index_name": NEO4J_VECTOR_INDEX,
        "top_k": 20,
    },
)


def get_mixtral_kwargs(prompt):
    kwargs = {
        "modelId": "mistral.mixtral-8x7b-instruct-v0:1",
        "contentType": "application/json",
        "accept": "*/*",
        "body": json.dumps(
            {
                "prompt": prompt,
                "max_tokens": 4096,
                "temperature": 0.5,
                "top_p": 0.9,
                "top_k": 50,
            }
        ),
    }
    return kwargs


# Replace this with updated keys if necessary
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
bedrock_runtime = session.client("bedrock-runtime", region_name="us-east-1")


def get_response(prompt):
    kwargs = get_mixtral_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get("body").read())
    return response_body["outputs"][0]["text"]


prompt = create_prompt(question, similar)

bedrock_response = get_response(prompt)

print(bedrock_response.strip())
