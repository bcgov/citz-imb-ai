from fastapi import APIRouter, Form
from app.models import neo4j, trulens, rag
from fastapi.responses import JSONResponse
import requests
import json
import os

router = APIRouter()

@router.get("/")
async def read_main():
    return {"msg": "Hello World"}

@router.get("/debug")
async def debug():
    print("Printing env variables")
    print(os.getenv("NEO4J_USERNAME"))
    print(os.getenv("AWS_SECRET_ACCESS_KEY"))
    print(os.getenv("AWS_ACCESS_KEY_ID"))
    print(os.environ)

@router.get("/login/")
async def login():
    #return JSONResponse(content={"valid": True})
    return {"valid": "True"}

@router.post("/refreshtoken/")
async def refresh_token(refresh_token: str = Form(...)):
    '''Refresh the token for the user'''
    endpoint = 'https://dev.loginproxy.gov.bc.ca/auth/realms/standard/protocol/openid-connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    print(refresh_token)
    data = {
        'client_id': 'a-i-pathfinding-project-5449',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(endpoint, headers=headers, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Token refresh failed")
    return response.json()

