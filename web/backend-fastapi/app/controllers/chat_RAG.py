from fastapi import APIRouter, Form
from app.dependencies import get_user_info
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models import neo4j, trulens, topK
import json

router = APIRouter()

@router.get("chat")
async def chat():
    return {"msg": "Hello World"}