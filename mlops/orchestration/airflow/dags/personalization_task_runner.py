from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago

import psycopg
from psycopg.rows import dict_row

import requests
import os
import json


# Simple connection class for Azure OpenAI
class AzureAI:
    def __init__(self, endpoint, key, response_token_max=1000):
        self.endpoint = endpoint
        self.key = key
        self.token_max = response_token_max

    def call(self, chat_chain):
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

# For later Postgres connection
pg_connection_string = f"""host={os.getenv("TRULENS_HOST")} dbname={os.getenv("APP_DB")} user={os.getenv("TRULENS_USER")} password={os.getenv("TRULENS_PASSWORD")} port={os.getenv("TRULENS_PORT")}"""

# These definitions are just examples to help the model understand what preferences could entail.
preference_definitions = {
    "communication_style": {
        "tone": "The overall mood and style of communication (e.g., casual, formal, professional, humorous, empathetic)",
        "response_length": "Preferred length of responses (e.g., concise, medium, detailed)",
        "format": "How information should be structured (e.g., paragraphs, bullets, numbered lists, tables)",
        "explanation_depth": "Level of detail in explanations (e.g., overview, deep_dive, balanced)",
        "uncertainty_handling": "How to handle uncertain or ambiguous situations (e.g., hedge, direct, best_guess)",
        "examples": "Type of examples to provide (e.g., neutral, personalized)",
    },
    "interaction_dynamics": {
        "proactivity": "How proactive the AI should be in offering suggestions (e.g., reactive, proactive, suggest_when_relevant)",
        "questions": "Approach to answering questions (e.g., direct_answer_first, guide_with_questions)",
        "error_handling": "How to handle errors or misunderstandings (e.g., clarify, just_say_dont_know)",
        "correction_handling": "How to respond when corrected (e.g., acknowledge, silently_adapt)",
        "follow_ups": "When to provide follow-up information (e.g., automatic, on_request)",
    },
    "content": {
        "topics_of_interest": "List of topics the user is particularly interested in",
        "jargon_level": "Preferred level of technical language (e.g., plain, technical, mixed)",
        "depth_preference": "User's expertise level for content depth (e.g., beginner, intermediate, expert)",
    },
    "practical": {
        "budget_awareness": "Consideration for cost in recommendations (e.g., cost_conscious, neutral, premium_friendly)",
        "tools": "List of preferred tools, platforms, or ecosystems",
        "units": "Preferred measurement system (e.g., metric, imperial)",
        "currency": "Preferred currency for financial information (e.g., USD, CAD, EUR)",
        "date_format": "Preferred date format (e.g., YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)",
        "time_format": "Preferred time format (e.g., 12h, 24h)",
    },
}

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


def update_chat_summaries(**context):
    # Set data structure track user changes while avoiding duplicates
    user_ids_to_update = set()
    # Postgres connection
    with psycopg.connect(
        pg_connection_string,
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
                user_ids_to_update.add(user_id)
                print(f"Chat ID {chat['id']} updated with new summary.")
                print(f"{len(user_ids_to_update)} unique users require update.")

                # Use Airflow XCom to pass user IDs to later steps
                # Convert set to list for serialization
                user_ids_list = list(str(user_id) for user_id in user_ids_to_update)
                context["task_instance"].xcom_push(key="user_ids", value=user_ids_list)


def create_user_summary(chat_summaries, existing_summary):
    # Create a combined summary prompt
    combined_summary_prompt = f"""
                    Based on the following chat summaries and previous user summary, create a concise user profile summary.
                    Include the user's interests, their common topics, and any other aspects that may be useful in later chats.
                    Prioritize recent information over older information.

                    Previous user summary:
                    {existing_summary}
                    
                    Here are the most recent chat summaries:
                    """ + "\n".join(
        [f"- {chat['summary']}" for chat in chat_summaries]
    )
    response = azure.call([{"role": "system", "content": combined_summary_prompt}])
    user_summary_text = response.get("message", {}).get("content", "").strip()
    return user_summary_text


def create_user_preferences(chat_summaries, existing_preferences):
    # Look at chat history for updates to preferences
    preferences_prompt = f"""
        Here are some definitions for sample preferences:
        {preference_definitions}

        Here are the user's current preferences:
        {existing_preferences}

        Here's the last few chats from this user:
        {chat_summaries}

        Based on this information, update the user's preferences if necessary and return the updated preferences as JSON.
        For example, if the user has mentioned a new interest or changed their communication style, reflect that in the preferences.
        If no changes are needed, return the existing preferences.
        Make sure to keep the format consistent with the original preferences.
        If the user requests a preference outside of the existing options, use your best judgement to update the preferences accordingly.
        You may add additional preference fields if needed, but keep the overall structure similar.
        Don't populate preferences with empty values or ones you haven't seen in the chat history.
        Don't populate the user preferences with definitions.
        Return no other information except the JSON object. No additional text, no explanations, no code block.
        """
    response = azure.call(
        [
            {
                "role": "system",
                "content": preferences_prompt,
            }
        ]
    )
    updated_preferences = response.get("message", {}).get("content", "").strip()
    return updated_preferences


def update_users(**context):
    user_ids = context["task_instance"].xcom_pull(
        key="user_ids", task_ids="update_chat_summaries"
    )
    if not user_ids:
        print("No user IDs to update.")
        return
    for user_id in user_ids:
        # Get the user's chat summaries
        with psycopg.connect(
            pg_connection_string,
            row_factory=dict_row,
        ) as conn:
            with conn.cursor() as db:
                db.execute(
                    """
                    SELECT summary
                    FROM chat
                    WHERE user_id = %s
                    AND summary IS NOT NULL
                    ORDER BY updated_at DESC
                    LIMIT 10
                    """,
                    (user_id,),
                )
                chat_summaries = db.fetchall()
                if not chat_summaries or len(chat_summaries) == 0:
                    print(
                        f"No chat summaries found for user ID: {user_id}, skipping..."
                    )
                    return
                print(f"Processing updates for user ID: {user_id}")
                # Get existing user info
                db.execute(
                    """
                    SELECT preferences, summary
                    FROM "user"
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                user_record = db.fetchone()
                existing_summary = user_record.get("summary", "")
                existing_preferences = user_record.get("preferences", {})
                # Generate new summary and preferences
                new_summary = create_user_summary(chat_summaries, existing_summary)
                new_preferences = create_user_preferences(
                    chat_summaries, existing_preferences
                )
                # Update the user's record with the new information
                db.execute(
                    """
                    UPDATE "user"
                    SET summary = %s, preferences = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (new_summary, new_preferences, user_id),
                )
                print(new_summary)
                print(new_preferences)
                print(f"Completed updates for user ID: {user_id}")


# Task definitions for the DAG
summarize_chats = PythonOperator(
    task_id="update_chat_summaries",
    python_callable=update_chat_summaries,
    dag=dag,
    provide_context=True,
)

update_users_fields = PythonOperator(
    task_id="update_users",
    python_callable=update_users,
    dag=dag,
    provide_context=True,
)

summarize_chats >> update_users_fields
