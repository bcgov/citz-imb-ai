#Do the migration
import os
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.docstore.document import Document
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import CharacterTextSplitter

#time.sleep(10)

##################### DATABASE CONNECTIONS ############################

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')

CONNECTION_STRING = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

########################################################################

##################### EXAMPLE EMBEDDINGS ############################
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
text = "This is a test document."
query_result = embeddings.embed_query(text)
doc_result = embeddings.embed_documents([text, "This is not a test document."])

##################### INITIALIZE EMBEDDINGS ############################
loader = TextLoader("DB/RawBCLaws/all_act_titles.txt")
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1, chunk_overlap=0, separator="\n")
docs = text_splitter.split_documents(documents)

COLLECTION_NAME = "bc_law_titles"

# If the database table already exists, delete it
db = PGVector.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    pre_delete_collection=True,
)

##################### Test the similarity search ###############################
query = "Is there a law on tenancy act?"
print('\n' + query + '\n')
docs_with_score = db.similarity_search_with_score(query)

for doc, score in docs_with_score:
    print("-" * 80)
    print("Score: ", score)
    print(doc.page_content)
    print("-" * 80)

#########################################################################

##################### INITIALIZE DOCSTORE ###############################
# If you want to connect to an existing collection  and test 
# the similarity search   
store = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
) 

query = "Is there any laws for landlords?"
print('\n' + query + '\n')
docs_with_score = store.similarity_search_with_score(query)

for doc, score in docs_with_score:
    print("-" * 80)
    print("Score: ", score)
    print(doc.page_content)
    print("-" * 80)


#########################################################################