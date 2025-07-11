import sys
from sentence_transformers import CrossEncoder
from langchain_community.embeddings import HuggingFaceEmbeddings


# Preload the model at application startup
# They are stored in cache allowing for faster lookup later
def preload_models():
    CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


preload_models()


class MockNestAsyncio:
    def apply(self):
        pass


sys.modules["nest_asyncio"] = MockNestAsyncio()

import asyncio
import uvloop

# Ensure uvloop is being used
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.logging import LoggingMiddleware
from app.controllers import feedback, chat_RAG, login, analytics
import warnings
import os
from dotenv import load_dotenv

from fastmcp import FastMCP
from app.mcp_agents import agents_mcp

warnings.filterwarnings("ignore")

app = FastAPI(root_path="/api")

# Include API routers
app.include_router(login.router)
app.include_router(feedback.router)
app.include_router(chat_RAG.router)
app.include_router(analytics.router)

# Register middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Get the ASGI-compliant app from your main MCP server instance
mcp_asgi_app = agents_mcp.http_app(path="/mcp", stateless_http=True, json_response=True)

# Mount the MCP app at the '/agents' endpoint
# Critical step: MUST pass the lifespan from the FastMCP app to FastAPI.
app.mount("/agents", mcp_asgi_app)
app.router.lifespan_context = mcp_asgi_app.lifespan

load_dotenv(
    "/vault/secrets/zuba-secret-dev"
)  # need to find soltion to load test and prod files in respective envs.

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=10000,
        timeout_keep_alive=120,  # 2 minutes timeout for keep-alive connections
        timeout_graceful_shutdown=120,  # 2 minutes timeout for graceful shutdown
    )
