from trulens_eval.tru_custom_app import instrument
from app.models import neo4j, trulens, rag, bedrock
import json
from typing import List

def retrieval(query_str, embeddings, kg):
    return neo4j.neo4j_vector_search(query_str, embeddings, kg)

class ChatHistory:
    def __init__(self, prompt: str, response: str):
        self.prompt = prompt
        self.response = response

class get_top_k:
    @instrument
    def retrieve(self, query: str, embeddings, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query, embeddings, kg)    

    @instrument
    def query(self, query: str, chat_history: List[ChatHistory], embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        return context_str

class get_full_rag:
    @instrument
    def retrieve(self, query: str, embeddings, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        print("retrieval processing")
        return retrieval(query, embeddings, kg)
    
    @instrument
    def create_prompt(self, query: str, context_str: str, chat_history: List[ChatHistory]) -> str:
        """
        Generate a response using the given context and chat history.
        """
        chat_history_str = "\n".join([f"Human: {ch.prompt}\nAI: {ch.response}" for ch in chat_history])
        print("chat_history_str: ", chat_history_str)
        messages = f"""
            You are a helpful and knowledgeable assistant. Use the following information to answer the user's question accurately and concisely. Do not provide information that is not supported by the given context or chat history.

            - Use the context and previous chat history to form your answer.
            - Laws and Acts can be used interchangeably.
            - If the answer is not found in the context or chat history, state that you don't know.
            - Do not attempt to fabricate an answer.

            Chat history:
            {chat_history_str}

            Context: 
            {context_str}

            Question: 
            {query}

            Provide the most accurate and helpful answer based on the information above. If no answer is found, state that you don't know.
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
            if 'references' in k:
                k_obj['references'] = k['references']
            prettier['topk'].append(k_obj)
        return prettier

    @instrument
    def query(self, query: str, chat_history: List[ChatHistory], embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        create_prompt = self.create_prompt(query, context_str, chat_history)
        bedrock_response = self.get_response(create_prompt)
        pretty_output = self.formatoutput(context_str, bedrock_response)
        return json.dumps(pretty_output)
