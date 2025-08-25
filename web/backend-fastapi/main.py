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
from app.modules.module_registry import module_registry
import warnings
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from app.shared.models.postgres import init_db_pool, close_db_pool

from fastmcp import FastMCP
from app.modules.agent.agents import agent_registry


warnings.filterwarnings("ignore")


@asynccontextmanager
async def pg_lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI to manage Postgres connection pool."""
    # Startup
    init_db_pool()
    yield
    # Shutdown
    close_db_pool()


app = FastAPI(root_path="/api", lifespan=pg_lifespan)

# Register all HMVC modules
module_registry.register_all_modules(app)

# Register middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Get the ASGI-compliant app from your main MCP server instance
combined_mcp = agent_registry.get_combined_mcp()
mcp_asgi_app = combined_mcp.http_app(
    path="/mcp", stateless_http=True, json_response=True
)

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
