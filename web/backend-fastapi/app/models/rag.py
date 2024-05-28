from trulens_eval.tru_custom_app import instrument
from app.models import neo4j, trulens, rag, bedrock
import json

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
    


class get_full_rag:
    @instrument
    def retrieve(self, query: str, embeddings, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query, embeddings, kg)
    
    @instrument
    def create_prompt(self, query: str, context_str) -> str:
        """
        Generate answer from context.
        """
        messages=f"""
            Use the following pieces of information to answer the user's question.
            Laws and Acts can be used interchangeably.
            If the answer is not in the documents, just say that you don't know. 
            Don't try to make up an answer.

            Context: 

            {context_str}

            Question: 

            {query}
            Only return the helpful answer below and nothing else.
        """
        return messages

    @instrument
    def get_response(self, query: str) -> str:
        bedrock_response = bedrock.get_response(query)
        return bedrock_response
    
    def formatoutput(self, topk, lm_output):
        prettier = {}
        prettier['llm'] = lm_output
        prettier['topk'] = []
        for k in topk:
            k_obj = {}
            k_obj['score'] = k['score']
            k_obj['ActId'] = k['node.ActId']
            k_obj['Regulations'] = k['Regulations']
            k_obj['sectionId'] = k['node.sectionId']
            k_obj['sectionName'] = k['node.sectionName']
            k_obj['url'] = k['node.url']
            k_obj['text'] = k['text']
            prettier['topk'].append(k_obj)
        return prettier

    @instrument
    def query(self, query: str, embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        create_prompt = self.create_prompt(query, context_str)
        bedrock_response = self.get_response(create_prompt)
        pretty_output = self.formatoutput(context_str, bedrock_response)
        return json.dumps(pretty_output)