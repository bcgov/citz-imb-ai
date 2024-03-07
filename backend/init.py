#Do the migration
import sqlalchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, insert, select, text, Integer
from sqlalchemy.orm import declarative_base, mapped_column, Session
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
import time

from langchain.docstore.document import Document
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import CharacterTextSplitter

time.sleep(10)

##################### DATABASE CONNECTIONS ############################

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')

sqlversion = sqlalchemy.__version__

connection_string = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

print(sqlversion)
#engine = create_engine("postgresql+psycopg://postgres:root@postgres:5432/ai_db")

engine = create_engine(connection_string)

with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    conn.commit()

Base = declarative_base()

########################################################################

##################### INITIALIZE EMBEDDINGS ############################
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
text = "This is a test document."
query_result = embeddings.embed_query(text)
doc_result = embeddings.embed_documents([text, "This is not a test document."])
print(doc_result)
loader = TextLoader("DB/RawBCLaws/all_act_titles.txt")

#########################################################################