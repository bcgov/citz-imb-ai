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
    # Only send atomic nodes as context
    # We do not want to send duplicate atomic nodes to the LLM
    # Use this dictionary like a Map of nodes. The key is the elementId.
    context_set = {}
    for record in context_str:
        atomic_nodes = record.get("atomicNodes", [])
        referenced_nodes = record.get("referencedNodes", [])
        next_nodes = record.get("nextNodes", [])
        for list in [atomic_nodes, referenced_nodes, next_nodes]:
            for node in list:
                node_id = node.get("elementId")
                if node_id and context_set.get(node_id) is None:
                    context_set[node_id] = node

    # Convert Map back to a list of nodes
    context = context_set.values()
    messages = f"""
            You are a helpful and knowledgeable assistant. Use the following information to answer the user's question accurately and concisely. Do not provide information that is not supported by the given context or chat history.

            - Use the context to form your answer.
            - Laws and Acts can be used interchangeably.
            - If the answer is not found in the context, state that you don't know.
            - Do not attempt to fabricate an answer.

            Context: 
            {context}

            Question: 
            {query}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
            In your responses, include references to where this piece of information came from.
            The format should always be (document_title, Section section_number (subsection_number)(paragraph_number)(subparagraph_number))
            Include the reference right after the information it provided.
            If information is from multiple parts of a Section, only reference the Section. For example, if info is from subsection 1, 2, and 3, only reference the Section.
            Not all references will have data for all these fields.
            Include nothing else in the reference.
            If you are not confident about what the reference should be, don't include it.
        """
    return messages


#### Adjust your question here ####
# question = "What does a yellow curb on the road mean?"
question = "Do I need to wear a seatbelt in BC?"
# question = "What is the fine for excessive speeding?"
# question = "How much notice do I need to give to end my rental lease in BC according to the Residential Tenancy Act?"

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
        RETURN score, node.ActId,  node.RegId as Regulations, node.sectionId, node.sectionName, node.url,  node.text AS text,
            collect(DISTINCT {elementId: elementId(atomicSection), containedProperties: properties(atomicSection)}) + collect(DISTINCT {elementId: elementId(containedNode), containedProperties: properties(containedNode)}) AS atomicNodes,
            collect(DISTINCT {elementId: elementId(refNode), referenceProperties: properties(refNode)}) AS referencedNodes,
            collect(DISTINCT {elementId: elementId(nextNode), nextProperties: properties(nextNode)}) AS nextNodes
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
