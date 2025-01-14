from bs4 import BeautifulSoup
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import time
from concurrent.futures import ThreadPoolExecutor
from langchain_community.graphs import Neo4jGraph
from pathlib import Path
from nodes import Act


token_splitter = SentenceTransformersTokenTextSplitter(
    chunk_overlap=50, tokens_per_chunk=256
)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Reading the data inside the xml
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


def process_act(file_name):
    if file_name == "":
        return
    print(f"{file_name} start")
    with open(f"{path}{file_name}", "r") as f:
        data = f.read()

    act_xml = BeautifulSoup(data, features="xml")
    try:
        ## Part 1 - Break Act into Nodes
        # Create Act Node
        act_node = Act(act_xml)

        ## Part 2 - Index Act and Add to Neo4j
        act_id = act_node.addNodeToDatabase(neo4j, token_splitter, embeddings)
    except Exception as e:
        print(f"Error in {file_name}: {e}")

    print(f"{file_name} end")


path = "examples/HTML_Acts/"
directory = Path(path)
# file_names = [f.name for f in directory.iterdir() if f.is_file()]
# file_names = ["Access_to_Abortion_Services_Act.xml", "Property_Transfer_Tax_Act.xml"]
file_names = [
    "Access_to_Abortion_Services_Act.xml",
    "Community_Charter_Transitional_Provisions_Consequential_Amendments_and_Other_Amendments_Act_2003.xml",
]

with ThreadPoolExecutor() as executor:
    print(f"Using {executor._max_workers} threads")
    list(executor.map(process_act, file_names))

end = time.time()
print(end - start)
