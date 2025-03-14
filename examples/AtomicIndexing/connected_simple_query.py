###
# Included this script so that I could test the indexing directly.
# This query uses the UpdatedChunk nodes for the semantic search, but then utilized the atomic nodes for information
# when sending context to the LLM.
# Initial feedback from use: responses are good and they can potentially include references to where each piece of info came from.
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
            In your responses, include references to where this piece of information came from. A reference will look like (Document Title, Section, Subsection, Paragraph, Subparagraph)
            Not all references will have data for all these fields. The order should always be Document Title, Section, Subsection, Paragraph, Subparagraph.
            Include nothing else in the reference.
            If you are not confident about what the reference should be, don't include it.
        """
    return messages


#### Adjust your question here ####
# question = "What is the meaning of a yellow curb?"
# question = "Do I need to wear a seatbelt in BC?"
question = "What is the fine for excessive speeding?"

query_embeddings = embeddings.embed_query(question)

# This vector query grabs a lot of connected nodes.
# It first does the semantic vector search on the index for UpdatedChunk nodes.
# It then finds the corresponding atomic section node, then pulls it and all its children
vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) 
        YIELD node, score
        OPTIONAL MATCH (node)-[:IS]-(atomicSection)
        OPTIONAL MATCH (atomicSection)-[:CONTAINS*]->(containedNode)
        OPTIONAL MATCH (containedNode)-[:NEXT*]->(nextNode)
        OPTIONAL MATCH (containedNode)-[:REFERENCE]->(refNode)
        RETURN 
            atomicSection,
            score, 
            collect(DISTINCT {containedProperties: properties(containedNode)}) AS containedNodes,
            collect(DISTINCT {referenceProperties: properties(refNode)}) AS referencedNodes,
            collect(DISTINCT {nextProperties: properties(nextNode)}) AS nextNodes
        ORDER BY score DESC
        """

NEO4J_VECTOR_INDEX = "Acts_Updatedchunks"
similar = neo4j.query(
    vector_search_query,
    params={
        "question": query_embeddings,
        "index_name": NEO4J_VECTOR_INDEX,
        "top_k": 10,
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
