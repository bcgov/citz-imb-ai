from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.logging import LoggingMiddleware
from app.controllers import feedback, chat_RAG, login
from app.models import neo4j, trulens, rag
import warnings
import os
from dotenv import load_dotenv
import threading

warnings.filterwarnings("ignore")

app = FastAPI(root_path="/api")

# Include API routers
app.include_router(login.router)
app.include_router(feedback.router)
app.include_router(chat_RAG.router)

# Register middleware
#app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

load_dotenv("/vault/secrets/zuba-secret-dev") # need to find soltion to load test and prod files in respective envs.

print("printing keys")
print(os.getenv("AWS_ACCESS_KEY_ID"))
print(os.getenv("AWS_SECRET_ACCESS_KEY"))
print(os.environ)

# Function to run the trulens dashboard in a separate thread
def run_trulens_dashboard():
    # Ensure you have set up the connection with trulens before running the dashboard
    tru = trulens.connect_trulens()
    tru.run_dashboard(port=14000)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=run_trulens_dashboard)
    thread.daemon = True
    thread.start()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*"
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
    uvicorn.run(app, host="0.0.0.0", port=10000)