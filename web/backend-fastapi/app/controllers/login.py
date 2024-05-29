from fastapi import APIRouter, Form
from app.models import neo4j, trulens, rag
import json

router = APIRouter()

@router.get("/")
async def read_main():
    return {"msg": "Hello World"}

@router.get("/login/")
async def login():
    return {"message": "Login successful"}

