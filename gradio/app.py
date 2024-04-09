import gradio as gr
import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from langchain.chains import RetrievalQAWithSourcesChain
import warnings
from langchain_community.document_loaders import DirectoryLoader
from llama_index.core import SimpleDirectoryReader, StorageContext
warnings.filterwarnings("ignore")
from langchain_community.embeddings import HuggingFaceEmbeddings
from trulens_eval import Tru
from trulens_eval.tru_custom_app import instrument
from llmlingua import PromptCompressor
from trulens_eval import Tru
from trulens_eval.tru_custom_app import instrument
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import torch
import time


# env variables:: to be set in the dockerfile 

NEO4J_URI = 'bolt://' + 'localhost' + ':7687'
NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = '12345678'
NEO4J_DATABASE = 'neo4j'

TRULENS_USER = 'postgres'
TRULENS_PASSWORD ='root'
TRULENS_DB = 'trulens'
TRULENS_PORT = '5432'
TRULENS_HOST = 'localhost'


# connect with the graph
kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

# connect with trulens
TRULENS_CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'
tru = Tru(database_url=TRULENS_CONNECTION_STRING)

# load embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

model_name = "./models/phi-1_5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def neo4j_vector_search(question):
  """Search for similar nodes using the Neo4j vector index"""
  query_embedding = embeddings.embed_query(question)  
  vector_search_query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
    RETURN score, node.ActId, node.RegId, node.text AS text
  """
  similar = kg.query(vector_search_query, 
                     params={
                      'question': query_embedding, 
                      'index_name':'Acts_chunks', 
                      'top_k': 10})
  return similar


  def retrieval(query_str):
    search_results = neo4j_vector_search(query_str)
    return search_results

def rerank(search_results):
    query = ''
    pairs = [[query, doc['text']] for doc in search_results]
    scores = cross_encoder.predict(pairs)
    # print("New Ordering:")
    for o in np.argsort(scores)[::-1]:
        print(o)   
        #print(search_results[o])
    return "( " + search_results[np.argsort(scores)[::-1][0]]['node.ActId']  + ')\n' + search_results[np.argsort(scores)[::-1][0]]['text'] + "\n\n( " + search_results[np.argsort(scores)[::-1][1]]['node.ActId']  + ')\n ' + search_results[np.argsort(scores)[::-1][1]]['text'] + "\n\n( " + search_results[np.argsort(scores)[::-1][2]]['node.ActId']  + ' )\n' + search_results[np.argsort(scores)[::-1][2]]['text']


# Kv chaching 

def generate_token_with_past(inputs):
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    last_logits = logits[0, -1, :]
    next_token_id = last_logits.argmax()
    return next_token_id, outputs.past_key_values


def generate(prompt, token_size=200):
    generated_tokens = []
    next_inputs = prompt
    durations_cached_s = []
    for _ in range(token_size):
        t0 = time.time()
        next_token_id, past_key_values = \
            generate_token_with_past(next_inputs)
        durations_cached_s += [time.time() - t0]
        
        next_inputs = {
            "input_ids": next_token_id.reshape((1, 1)),
            "attention_mask": torch.cat(
                [next_inputs["attention_mask"], torch.tensor([[1]])],
                dim=1),
            "past_key_values": past_key_values,
        }
        
        next_token = tokenizer.decode(next_token_id)
        generated_tokens.append(next_token)
    print(f"{sum(durations_cached_s)} s")
    return ''.join(generated_tokens)
# 
# print(generated_tokens)

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query)

    @instrument
    def reranked(self, search_results) -> str:
        return rerank(search_results)

    def genprompt(self, query: str, context_str: list) -> str:
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
    def promptcompression(self, prompt, query) ->str:
        compressed_prompt = llm_lingua.compress_prompt(prompt, instruction="", question="", target_token=200)
        return compressed_prompt['compressed_prompt']

    @instrument
    def generate_completion(self, compressed_prompt:str) -> str:
        print(compressed_prompt)
        completion = asyncio.run(main(compressed_prompt))
        return completion

    @instrument
    def query(self, query: str) -> str:
        context_str = self.retrieve(query)
        rerank = self.reranked(context_str)
        prompt = self.genprompt(query, rerank)
        print(prompt)
        compressed_prompt = self.promptcompression(prompt, query)
        # tokenize
        inputs = tokenizer(prompt, return_tensors="pt")
        completion = generate(inputs)
        return completion

rag = RAG_from_scratch()

def llm_function(message):
    return rag.query(message)


title = "BC law buddy 🗨️"
description = "A large language model that can help you find information about BC laws. Ask it a question and it will find the most relevant information for you. 📚🔍🗨️"


demo = gr.Interface(
    fn=llm_function,
    inputs=["text"],
    outputs=["text"],
    title=title, description=description
)


demo.launch(server_name="0.0.0.0", server_port=9999)