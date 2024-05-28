import boto3
import json

session = boto3.Session()
bedrock_runtime = session.client('bedrock-runtime', region_name='us-east-1')

def get_kwargs(prompt):
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
                "top_k": 50
            }
        )
    }
    return kwargs

def get_response(prompt):
    kwargs = get_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get('body').read())
    return response_body['outputs'][0]['text']