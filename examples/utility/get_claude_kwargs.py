import json
import boto3
import os
import sys

# Use os.getcwd() since __file__ is not available in interactive environments
current_dir = os.getcwd()

# If your structure is such that the package is in the parent directory, compute the parent directory:
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

# Add the parent directory to sys.path if it's not already there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from AgenticWorkflow.bedrock_session import get_boto_session
session = get_boto_session()

# Initialize AWS session and Bedrock runtime client
# Configure Bedrock runtime for us-east-1 region
bedrock_runtime = session.client("bedrock-runtime", region_name="us-east-1")

def get_claude_kwargs(prompt):
    kwargs = {
      "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "contentType": "application/json",
      "accept": "application/json",
      "body": json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10000,
        "messages": [
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": prompt
              }
            ]
          }
        ]
      })
    }
    return kwargs

def get_response(prompt):
    kwargs = get_claude_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get("body").read())
    return response_body['content'][0]['text']