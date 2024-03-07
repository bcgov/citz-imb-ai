#Do the migration
import sqlalchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, insert, select, text, Integer
from sqlalchemy.orm import declarative_base, mapped_column, Session
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')

print(POSTGRES_USER)

#print(os.environ['HOME'])
#POSTGRES_USER = os.environ['POSTGRES_USER']
#POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
#POSTGRES_DB = os.environ['POSTGRES_DB']

sqlversion = sqlalchemy.__version__
print(sqlversion)
engine = create_engine("postgresql+psycopg://postgres:root@postgres:5432/ai_db")
with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    conn.commit()

Base = declarative_base()

