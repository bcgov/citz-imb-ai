import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory to sys.path to find main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
