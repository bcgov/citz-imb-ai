from bs4 import BeautifulSoup
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import time
from concurrent.futures import ThreadPoolExecutor
from langchain_community.graphs import Neo4jGraph
from pathlib import Path
from nodes import Act, Regulation
from threading import current_thread
import traceback

# Set up embeddings and database connection
token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=50, tokens_per_chunk=256
)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

start = time.time()

NEO4J_URI = "bolt://" + "localhost:7687"  # os.getenv("NEO4J_HOST") + ":7687"
NEO4J_USERNAME = "admin"  # os.getenv("NEO4J_USER")
NEO4J_PASSWORD = "admin"  # os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = "neo4j"  # os.getenv('NEO4J_DB')

neo4j = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)

version_tag = "v3"


# Function to process and index an act
def process_act(file_name):
    if file_name == "":
        return
    thread = current_thread().getName()
    print(f"Thread {thread}: {file_name} start")
    with open(f"{acts_path}{file_name}", "r") as f:
        data = f.read()

        act_xml = BeautifulSoup(data, features="xml")
        try:
            ## Part 1 - Break Act into Nodes
            act_node = Act(version_tag, act_xml)

            ## Part 2 - Index Act and Add to Neo4j
            act_id = act_node.addNodeToDatabase(neo4j, token_splitter, embeddings)
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            print(traceback.format_exc())

    print(f"Thread {thread}: {file_name} end")


# Function to process and index a regulation
def process_regulation(file_name):
    if file_name == "":
        return
    thread = current_thread().getName()
    print(f"Thread {thread}: {file_name} start")
    with open(f"{regs_path}{file_name}", "r") as f:
        data = f.read()

        reg_xml = BeautifulSoup(data, features="xml")
        try:
            ## Part 1 - Break Regulation into Nodes
            reg_node = Regulation(version_tag, reg_xml)

            ## Part 2 - Index Regulation and Add to Neo4j
            reg_id = reg_node.addNodeToDatabase(neo4j, token_splitter, embeddings)
        except Exception as e:
            print(f"Error in {file_name}: {e}")
            print(traceback.format_exc())

    print(f"Thread {thread}: {file_name} end")


acts_path = "examples/HTML_Acts/"
act_directory = Path(acts_path)
act_file_names = [f.name for f in act_directory.iterdir() if f.is_file()]

regs_path = "examples/HTML_Regulations/"
reg_directory = Path(regs_path)
reg_file_names = [f.name for f in reg_directory.iterdir() if f.is_file()]

with ThreadPoolExecutor() as executor:
    print(f"Using {executor._max_workers} threads")
    list(executor.map(process_act, act_file_names))
    list(executor.map(process_regulation, reg_file_names))

# Add vector indexes
# https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
# NOTE: 384 vector dimensions seemed to work in local testing, but 256 didn't.
index_query = f"""
CREATE VECTOR INDEX content_embedding_{version_tag} IF NOT EXISTS
FOR (m:Content_{version_tag})
ON m.text_embedding
OPTIONS {{ indexConfig: {{ `vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}} }}
"""
neo4j.query(index_query)

end = time.time()
print(end - start)
