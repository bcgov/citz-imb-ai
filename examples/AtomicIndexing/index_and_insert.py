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

    ## Part 1 - Break Act into Nodes

    act_title = act_xml.find("act:title").getText()
    act_chapter = act_xml.find("act:chapter").getText()
    act_year = act_xml.find("act:yearenacted").getText()

    # Create Act Node
    act_node = Act(act_title, act_chapter, act_year)

    act_content = act_xml.find("act:content")

    # For each section, log metadata, create node
    sections = act_content.find_all("bcl:section", recursive=False)

    for section in sections:
        act_node.addSection(section)

    ## Part 2 - Add Act to Neo4j
    act_id = act_node.addNodeToDatabase(neo4j)

    ## Part 3 - Add Content Nodes to Neo4j
    for section in act_node.sections:
        section_id = section.addNodeToDatabase(
            neo4j, act_id, token_splitter, embeddings, {"title": section.title}
        )
        for subsection in section.subsections:
            subsection_id = subsection.addNodeToDatabase(
                neo4j,
                section_id,
                token_splitter,
                embeddings,
            )
            for paragraph in subsection.paragraphs:
                paragraph_id = paragraph.addNodeToDatabase(
                    neo4j,
                    subsection_id,
                    token_splitter,
                    embeddings,
                )
                for subparagraph in paragraph.subparagraphs:
                    subparagraph.addNodeToDatabase(
                        neo4j,
                        paragraph_id,
                        token_splitter,
                        embeddings,
                    )
        for paragraph in section.paragraphs:
            paragraph_id = paragraph.addNodeToDatabase(
                neo4j,
                section_id,
                token_splitter,
                embeddings,
            )
            for subparagraph in paragraph.subparagraphs:
                subparagraph.addNodeToDatabase(
                    neo4j,
                    paragraph_id,
                    token_splitter,
                    embeddings,
                )
        for definition in section.definitions:
            definition.addNodeToDatabase(neo4j, section_id)

    print(f"{file_name} end")


path = "examples/HTML_Acts/"
directory = Path(path)
# file_names = [f.name for f in directory.iterdir() if f.is_file()]
file_names = ["Access_to_Abortion_Services_Act.xml"]
with ThreadPoolExecutor() as executor:
    print(f"Using {executor._max_workers} threads")
    list(executor.map(process_act, file_names))

end = time.time()
print(end - start)
