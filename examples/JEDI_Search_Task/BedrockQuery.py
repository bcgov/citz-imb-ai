import json
import boto3


class BedrockQuery:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        self.bedrock_runtime = session.client(
            "bedrock-runtime", region_name="us-east-1"
        )

    # Standard kwargs for claude
    def get_claude_kwargs(self, prompt):
        kwargs = {
            "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 5000,
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": prompt}]}
                    ],
                }
            ),
        }
        return kwargs

    def get_response(self, prompt):
        kwargs = self.get_claude_kwargs(prompt)
        response = self.bedrock_runtime.invoke_model(**kwargs)
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]
