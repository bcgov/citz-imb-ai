import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv("/vault/secrets/zuba-secret-dev")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
bedrock_runtime = session.client("bedrock-runtime", region_name="us-east-1")


def get_mixtral_kwargs(prompt):
    kwargs = {
        "modelId": "mistral.mixtral-8x7b-instruct-v0:1",
        "contentType": "application/json",
        "accept": "*/*",
        "body": json.dumps(
            {
                "prompt": prompt,
                "max_tokens": 1024,
                "temperature": 0.5,
                "top_p": 0.9,
                "top_k": 50,
            }
        ),
    }
    return kwargs


def get_lama3_kwargs(prompt):
    kwargs = {
        "modelId": "meta.llama3-8b-instruct-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps(
            {
                "prompt": prompt,
                "temperature": 0.5,
                "top_p": 0.9,
                "max_gen_len": 1024,
            }
        ),
    }
    return kwargs


def get_response(prompt):
    kwargs = get_mixtral_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get("body").read())
    return response_body["outputs"][0]["text"]
