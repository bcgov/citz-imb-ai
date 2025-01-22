###
# Included this script so that I could test the indexing directly.
###

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.graphs import Neo4jGraph
import os
import json
import boto3

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

NEO4J_URI = "bolt://" + "localhost:7687"  # os.getenv("NEO4J_HOST") + ":7687"
NEO4J_USERNAME = "admin"  # os.getenv("NEO4J_USER")
NEO4J_PASSWORD = "admin"  # os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = "neo4j"  # os.getenv('NEO4J_DB')

neo4j = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)


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
question = "Do I have to wear a seatbelt in BC?"

query_embeddings = embeddings.embed_query(question)

vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) 
        YIELD node, score
        OPTIONAL MATCH (node)-[:REFERENCES]->(refNode)
        OPTIONAL MATCH (node)-[:CONTAINS]->(containedNode)
        OPTIONAL MATCH (parent)-[:CONTAINS]->(node) // Find the parent of the node
        OPTIONAL MATCH (parent)-[:CONTAINS]->(siblingNode) 
        WHERE node <> siblingNode // Exclude the node itself from its siblings
        RETURN 
            score, 
            node.text AS text,
            collect(DISTINCT {refText: refNode.text}) AS references,
            collect(DISTINCT {containedText: containedNode.text}) AS containedNodes,
            collect(DISTINCT {siblingText: siblingNode.text}) AS siblings
        ORDER BY score DESC
        """

NEO4J_VECTOR_INDEX = "content_embedding"
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
                "max_tokens": 1024,
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


prompt = create_prompt(query_embeddings, similar)
bedrock_response = get_response(prompt)

print(bedrock_response)
