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
from sentence_transformers import CrossEncoder
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
# TRULENS_CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'
# tru = Tru(database_url=TRULENS_CONNECTION_STRING)

# load embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

model_name = "/Users/msihag/repos/citz-imb-ai/backend/models/phi-2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def neo4j_vector_search(question, index):
  """Search for similar nodes using the Neo4j vector index"""
  query_embedding = embeddings.embed_query(question)  
  vector_search_query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
    RETURN score, node.ActId, node.RegId, node.sectionName, node.sectionId, node.text AS text
  """
  similar = kg.query(vector_search_query, 
                     params={
                      'question': query_embedding, 
                      'index_name':index, 
                      'top_k': 10})
  return similar

## Or use LLMLingua-2-small model
# llm_lingua = PromptCompressor(
#     model_name="/Users/msihag/repos/citz-imb-ai/backend/models/phi-2",
#     #use_llmlingua2=True, # Whether to use llmlingua-2,
#     device_map="cpu"
# )

def retrieval(query_str):
    search_results = neo4j_vector_search(query_str, 'Acts_Updatedchunks')
    return search_results

def rerank(search_results, query):
    pairs = [[query, doc['text']] for doc in search_results]
    scores = cross_encoder.predict(pairs)
    # print("New Ordering:")
    # for o in np.argsort(scores)[::-1]:
    #     print(o)   
    #     #print(search_results[o])
    return "Act Id:  " + search_results[np.argsort(scores)[::-1][0]]['node.ActId'] + '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][0]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][0]]['node.sectionId'] + '\n' + search_results[np.argsort(scores)[::-1][0]]['text'] + "\n\n"+"Act Id:  " + search_results[np.argsort(scores)[::-1][1]]['node.ActId']+ '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][1]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][1]]['node.sectionId'] + '\n' + search_results[np.argsort(scores)[::-1][1]]['text'] + "\n\n"+"Act Id:  " + search_results[np.argsort(scores)[::-1][2]]['node.ActId']+ '\n' + "Section Name: " + search_results[np.argsort(scores)[::-1][2]]['node.sectionName'] + '\n' + "Section Id: " + search_results[np.argsort(scores)[::-1][2]]['node.sectionId'] + '\n' + search_results[np.argsort(scores)[::-1][2]]['text'] 

# Kv chaching 

def generate_token_with_past(inputs):
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    last_logits = logits[0, -1, :]
    next_token_id = last_logits.argmax()
    return next_token_id, outputs.past_key_values




def generate(prompt, token_size=500):
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
        #print(next_token)
        # generated_tokens.append(next_token)
        yield next_token
    print(f"{sum(durations_cached_s)} s")
    # return ''.join(generated_tokens)

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query)

    @instrument
    def reranked(self, search_results, query) -> str:
        return rerank(search_results, query)

    def genprompt(self, query: str, context_str: list) -> str:
        """
        Generate answer from context.
        """
        messages=f"""

Context: 

{context_str}

user's question: 

{query}

Use the above pieces of information to answer the user's question.

If the answer is not in the context, just say "I don't know". 
Don't try to make up an answer.

Answer:
                    """
        return messages
        
    @instrument 
    def promptcompression(self, prompt, query) ->str:
        compressed_prompt = llm_lingua.compress_prompt(prompt, instruction="", question="", target_token=1000)
        return compressed_prompt['compressed_prompt']

    @instrument
    def generate_completion(self, compressed_prompt:str) -> str:
        print(compressed_prompt)
        completion = asyncio.run(main(compressed_prompt))
        return completion

    @instrument
    def query(self, query: str, history) -> str:
        context_str = self.retrieve(query)
        rerank = self.reranked(context_str, query)
        prompt = self.genprompt(query, rerank)
        # print(prompt)
        # compressed_prompt = self.promptcompression(prompt, query)
        # tokenize
        # print(compressed_prompt)
        inputs = tokenizer(prompt, return_tensors="pt")
        text = ''
        for i in generate(inputs):
            text += i
            print(text)
            yield text

rag = RAG_from_scratch()


def vote(data: gr.LikeData):
    if data.liked:
        print("You upvoted this response: " + data.value)
    else:
        print("You downvoted this response: " + data.value)


title = "BC law"
description = "Try asking a question about BC law and it will return the most relevant section of the law."



demo = gr.ChatInterface(
        fn=rag.query,
        title=title, description=description,
        theme = "soft"
        )


demo.launch(server_name="0.0.0.0", server_port=9995, share=True)