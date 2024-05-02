import gradio as gr
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
import warnings
warnings.filterwarnings("ignore")
from langchain_community.embeddings import HuggingFaceEmbeddings
from llmlingua import PromptCompressor
from sentence_transformers import CrossEncoder
import numpy as np
import time

from meta_ai_api import MetaAI
ai = MetaAI()


NEO4J_URI = 'bolt://8.tcp.us-cal-1.ngrok.io:10651'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = '12345678'
NEO4J_DATABASE = 'neo4j'

# connect with the graph
kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

embeddings = HuggingFaceEmbeddings(model_name="mixedbread-ai/mxbai-embed-large-v1")

cross_encoder = CrossEncoder('mixedbread-ai/mxbai-rerank-large-v1')


def neo4j_vector_search(question, index):
    """Search for similar nodes using the Neo4j vector index"""
    query_embedding = embeddings.embed_query(question)  
    vector_search_query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
    RETURN score, node.ActId, node.summary, node.sectionName, node.sectionId, node.RegId, node.text AS text
    """
    similar = kg.query(vector_search_query, 
                     params={
                      'question': query_embedding, 
                      'index_name':index, 
                      'top_k': 10})
    return similar


def retrieval(query_str):
    search_results = neo4j_vector_search(query_str, 'Acts_summary_chunks')
    return search_results

def rerank(search_results, query):
    pairs = [[query, doc['text']] for doc in search_results]
    scores = cross_encoder.predict(pairs)
    # print("New Ordering:")
    # for o in np.argsort(scores)[::-1]:
    #     print(o)   
    #     #print(search_results[o])
    return "Act Id:  " + search_results[np.argsort(scores)[::-1][0]]['node.ActId'] + '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][0]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][0]]['node.sectionId'] + '\n' + "Summary: " + search_results[np.argsort(scores)[::-1][0]]['node.summary'] + "\n\n"+"Act Id:  " + search_results[np.argsort(scores)[::-1][1]]['node.ActId']+ '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][1]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][1]]['node.sectionId'] + '\n' + "Summary: " + search_results[np.argsort(scores)[::-1][1]]['node.summary'] + "\n\n"+"Act Id:  " + search_results[np.argsort(scores)[::-1][2]]['node.ActId']+ '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][2]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][2]]['node.sectionId'] + '\n' + "Summary" + search_results[np.argsort(scores)[::-1][2]]['node.summary']


class RAG_from_scratch:
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query)

    def reranked(self, search_results, query) -> str:
        return rerank(search_results, query)

    def genprompt(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        messages=f"""
Use the following pieces of information to answer the user's question.
Laws and Acts can be used interchangeably.
If the answer is not in the documents, just say that you don't know. 
Don't try to make up an answer. dont write Question/Answer, just write the answer when done stop generating text.

Context: 

{context_str}

Question: 

{query}
Only return the helpful answer below and nothing else.
                    """
        return messages
        
    def promptcompression(self, prompt, query) ->str:
        compressed_prompt = llm_lingua.compress_prompt(prompt, instruction="", question="", target_token=1000)
        return compressed_prompt['compressed_prompt']

    def generate_completion(self, compressed_prompt:str) -> str:
        print(compressed_prompt)
        completion = asyncio.run(main(compressed_prompt))
        return completion

    def query(self, query: str, history) -> str:
        context_str = self.retrieve(query)
        rerank = self.reranked(context_str, query)
        return rerank
        # prompt = self.genprompt(query, rerank)
        # response = ai.prompt(message=prompt)
        # return response["message"]
        # prompt = self.genprompt(query, rerank)
        # print(prompt)
        # compressed_prompt = self.promptcompression(prompt, query)
        # tokenize
        # print(compressed_prompt)
        # inputs = tokenizer(prompt, return_tensors="pt")
        # text = ''
        # for i in generate(inputs):
        #     text += i
        #     print(text)
        #     yield text

rag = RAG_from_scratch()


title = "BC law"
description = "Try asking a question about BC law and it will return the most relevant section of the law."


demo = gr.ChatInterface(
        fn=rag.query,
        title=title, description=description,
        theme = "soft"
        )


demo.launch(server_name="0.0.0.0", server_port=9998, share=True)