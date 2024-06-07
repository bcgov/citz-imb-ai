from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.authentication import AuthenticationMiddleware
from app.middleware.logging import LoggingMiddleware
from app.controllers import feedback, chat_RAG, login
import warnings
import os
warnings.filterwarnings("ignore")

app = FastAPI(root_path="/api")

# Include API routers
app.include_router(login.router)
app.include_router(feedback.router)
app.include_router(chat_RAG.router)

# Register middleware
#app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)


print("Printing env variables")
print(os.getenv("NEO4J_USERNAME"))
print(os.getenv("AWS_SECRET_ACCESS_KEY"))
print(os.getenv("AWS_ACCESS_KEY_ID"))
print(os.environ)

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