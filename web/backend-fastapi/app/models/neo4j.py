from langchain_community.graphs import Neo4jGraph
import os

def neo4j_vector_search(question, embeddings, kg):
    """Search for similar nodes using the Neo4j vector index"""
    query_embedding = embeddings.embed_query(question)
    vector_search_query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
        OPTIONAL MATCH (node)-[:REFERENCES]->(refNode)
        RETURN score, 
                node.ActId AS ActId,  
                node.RegId as Regulations, 
                node.sectionId AS sectionId, 
                node.sectionName AS sectionName, 
                node.url AS url,
                node.file_name AS file_name,
                node.folder AS folder,
                node.section AS section,
                node.subfolder AS subfolder,
                node.type AS type,
                node.text AS text,
                collect({
                    refSectionId: refNode.sectionId, 
                    refSectionName: refNode.sectionName, 
                    refActId: refNode.ActId, 
                    refText: refNode.text
                }) AS references
        ORDER BY score DESC
    """
    NEO4J_VECTOR_INDEX = os.getenv('NEO4J_VECTOR_INDEX')
    similar = kg.query(vector_search_query,
                        params={
                            'question': query_embedding,
                            'index_name': NEO4J_VECTOR_INDEX,
                            'top_k': 10})
    return similar

def neo4j():
    NEO4J_URI = 'bolt://citz-imb-ai-neo4j-svc:7687'
    NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    NEO4J_DB = os.getenv('NEO4J_DB')
    kg = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DB)
    return kg
