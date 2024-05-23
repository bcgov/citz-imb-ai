from fastapi import APIRouter, Form
from app.dependencies import get_user_info
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models import neo4j, trulens, topK
import json

router = APIRouter()
kg = None
tru = None
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@router.get("chat")
async def chat(prompt: str = Form(...)):
    # Global variables initialization
    global kg, tru, APP_ID
    rag = topK.get_top_k()
    if kg is None:
        kg = neo4j.neo4j()
    if tru is None:
        tru = trulens.connect_trulens()
    tru_rag = trulens.tru_rag(rag)
    print(tru_rag)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    with tru_rag as recording:
        responses = rag.query(prompt, embeddings, kg)
    record = recording.get()
    import requests
url = 'https://LLMSErver.a0a6fc-prod.nimbus.cloud.gov.bc.ca/v1/chat/completions'
headers = {'Content-Type': 'application/json'}
data = '{"model": "Intel/neural-chat-7b-v3-1", "messages": [ \
          {"role": "system", "content": "You are a helpful assistant."}, \
          {"role": "user", "content": "{prompt}"}], \
           "stream":"True"}'
response = requests.post(url, headers=headers, data=data)
print(response.json())
    