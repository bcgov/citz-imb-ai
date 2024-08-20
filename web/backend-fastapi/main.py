import sys


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

warnings.filterwarnings("ignore")

app = FastAPI(root_path="/api")

# Include API routers
app.include_router(login.router)
app.include_router(feedback.router)
app.include_router(chat_RAG.router)
app.include_router(analytics.router)

# Register middleware
# app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

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
