from typing import List
from fastapi import APIRouter, Body, Request, Response
from pydantic import BaseModel
from fastmcp import Client
from ..mcp_agents import agents_mcp

router = APIRouter()


class AgentHistory(BaseModel):
    prompt: str
    response: str


class AgentRequest(BaseModel):
    prompt: str
    # chatHistory: List[AgentHistory]


@router.post("/test/")
async def agentic_chat(request: Request = None):
    print(
        "Received agentic chat request:",
        await request.json() if request else None,
        flush=True,
    )
    # Call internal route, /agents/mcp
    # if not isinstance(chat_request, AgentRequest):
    #     raise ValueError("Input should be a valid AgentRequest object")

    # Make internal HTTP call
    client = Client(agents_mcp)
    async with client:
        data = await client.list_tools()
        return {"is_connected": client.is_connected(), "tools": data}
