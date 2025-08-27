from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

import psycopg
from psycopg.rows import dict_row

import requests
import os
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


# Azure Connection
endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
key = os.getenv("AZURE_AI_KEY", "")
azure = AzureAI(endpoint, key)

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

# Define the DAG
dag = DAG(
    "personalization_task_runner",
    default_args=default_args,
    description="Summarize outstanding chat messages, create user summaries, and save user preferences",
    schedule_interval="@hourly",
    start_date=days_ago(1),
    catchup=False,
)

# Global list to track user IDs that need updates
# This should be a Set data structure to avoid duplicates
user_ids_to_update = set()


def update_chat_summaries():
    # Postgres connection
    with psycopg.connect(
        f"""host={os.getenv("TRULENS_HOST")} dbname={os.getenv("APP_DB")} user={os.getenv("TRULENS_USER")} password={os.getenv("TRULENS_PASSWORD")} port={os.getenv("TRULENS_PORT")}""",
        row_factory=dict_row,
    ) as conn:
        with conn.cursor() as db:
            # Get all chats that need summarization
            # A chat needs a new summary if the current summary is null
            # OR if the difference between the updated_at column and the last timestamp in the chat_chain is more than 5 minutes.
            # If the record was updated by a user expanding the chat, these values will be milliseconds apart.
            # If the value is farther apart, it means this record was updated by the previous summarization and the chat has not changed since
            db.execute(
                """
                SELECT *
                FROM chat
                WHERE chat_chain IS NOT NULL
                AND (summary IS NULL
                OR (
                    updated_at <= (
                        SELECT MAX((message->>'timestamp')::timestamptz)
                        FROM jsonb_array_elements(chat_chain) AS message
                    ) + INTERVAL '5 minutes'
                ))
                """
            )
            chats_to_summarize = db.fetchall()
            print(f"Found {len(chats_to_summarize)} chats to summarize.")
            for chat in chats_to_summarize:
                print(f"Summarizing chat ID: {chat['id']}")
                chat_chain = chat["chat_chain"]
                if not chat_chain or len(chat_chain) == 0:
                    print("No chat chain found, skipping...")
                    continue

                # Call Azure AI to summarize the chat
                summary_prompt = """
                    Summarize the following chat. Keep this summary concise.
                    Format this summary describing what the user asked for and
                    what the assistant was able to provide.
                    If the user asked for changes to their preferences or how the assistant should respond, 
                    include that at the end of the summary. If they didn't request any changes, don't mention it.

                    For example:
                    The user asked about laws regarding the use of AI.
                    The assistant provided information on the current state of AI legislation.
                    The user requested that the assistant talk in a less-technical manner.
                    """ + json.dumps(
                    chat_chain, indent=2
                )
                summary = azure.call([{"role": "system", "content": summary_prompt}])
                summary_text = summary["message"]["content"].strip()
                print(f"Summary: {summary_text}")

                # Update the chat record with the new summary
                db.execute(
                    """
                    UPDATE chat
                    SET summary = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING user_id
                    """,
                    (summary_text, chat["id"]),
                )
                user_id = db.fetchone()["user_id"]
                if user_id not in user_ids_to_update:
                    user_ids_to_update.add(user_id)
                print(f"Chat ID {chat['id']} updated with new summary.")


def update_user_summaries():
    # Placeholder function to create user summaries
    print("Creating user summaries...")
    # Actual implementation would go here
    pass


def update_user_preferences():
    # Placeholder function to create user preferences
    print("Creating user preferences...")
    # Actual implementation would go here
    pass


# Task definitions for the DAG
summarize_chats = PythonOperator(
    task_id="update_chat_summaries",
    python_callable=update_chat_summaries,
    dag=dag,
)

user_summaries = PythonOperator(
    task_id="update_user_summaries",
    python_callable=update_user_summaries,
    dag=dag,
)

user_preferences = PythonOperator(
    task_id="update_user_preferences",
    python_callable=update_user_preferences,
    dag=dag,
)

summarize_chats >> user_summaries >> user_preferences
