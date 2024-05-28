from trulens_eval.tru_custom_app import instrument

def neo4j_vector_search(question, embeddings, kg):
  """Search for similar nodes using the Neo4j vector index"""
  query_embedding = embeddings.embed_query(question)
  vector_search_query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
    RETURN score, node.ActId,  node.RegId as Regulations, node.sectionId, node.sectionName, node.url,  node.text AS text
  """
  similar = kg.query(vector_search_query, 
                     params={
                      'question': query_embedding, 
                      'index_name':'Acts_Updatedchunks', 
                      'top_k': 10})
  return similar

def retrieval(query_str):
    return neo4j_vector_search(query_str)

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query)    

    @instrument 
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        return context_str
