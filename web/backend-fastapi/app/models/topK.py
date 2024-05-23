from trulens_eval.tru_custom_app import instrument
from app.models import neo4j, trulens, topK

def retrieval(query_str, embeddings, kg):
    return neo4j.neo4j_vector_search(query_str, embeddings, kg)

class get_top_k:
    @instrument
    def retrieve(self, query: str, embeddings, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query, embeddings, kg)    

    @instrument
    def query(self, query: str, embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        return context_str