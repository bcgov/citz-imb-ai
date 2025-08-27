import requests
import json


class AzureAI:
    def __init__(self, endpoint, key, response_token_max=1000):
        self.endpoint = endpoint
        self.key = key
        self.token_max = response_token_max

    def call(self, chat_chain):
        """Supported values for role: 'system', 'assistant', 'user', 'function', 'tool', and 'developer'"""
        headers = {"Content-Type": "application/json", "api-key": self.key}
        body = {
            "messages": chat_chain,
            "max_tokens": self.token_max,
        }

        response = requests.post(self.endpoint, headers=headers, json=body, timeout=30)

        if response.status_code == 200:
            choice = response.json().get("choices")[0]
            return choice
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
