# Test to see how we can summarize a user based on their chat history and update their preferences.
# Uses Azure OpenAI and gets/saves data to Postgres.

from AzureSimple import AzureAI
from datetime import datetime, timezone
import os
import psycopg
from psycopg.rows import dict_row
from sample_preferences import default_preferences, preference_definitions

# Azure Connection
endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
key = os.getenv("AZURE_AI_KEY", "")
azure = AzureAI(endpoint, key)

# Fake uuid for testing
user_id = "00000000-0000-0000-0000-000000000000"

# Local Postgres connection
with psycopg.connect(
    "host=localhost dbname=postgres user=postgres password=root port=5433",
    row_factory=dict_row,
) as conn:
    with conn.cursor() as db:
        db.execute(
            f"""
            SELECT * 
            FROM \"user\" 
            WHERE id = '{user_id}'
            """
        )
        my_user = db.fetchone()
        # Get last 10 chats for this user
        db.execute(
            f"""
            SELECT * 
            FROM chat 
            WHERE user_id = '{user_id}' 
            ORDER BY created_at DESC 
            LIMIT 10
            """
        )
        last_chats = db.fetchall()

        # Get only the summaries from the last chats
        chat_summaries = [chat["summary"] for chat in last_chats if chat.get("summary")]
        summary_prompt = f"""
        Here are the summaries of the last 10 chats:
        {chat_summaries}

        Summarize a bit about the user based on these chats.
        """

        response = azure.call(
            [
                {
                    "role": "system",
                    "content": summary_prompt,
                }
            ]
        )

        user_summary = response.get("message", {}).get("content", "").strip()
        print("User Summary:", user_summary)

        # Rebuild the user preferences as well
        my_user_preferences = my_user.get("preferences", {})

        # Look at chat history for updates to preferences
        preferences_prompt = f"""
        Here are some definitions for sample preferences:
        {preference_definitions}

        Here are the user's current preferences:
        {my_user_preferences}

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
        print("Updated Preferences:", updated_preferences)

        # Update user in the database
        db.execute(
            """
            UPDATE "user"
            SET preferences = %s, summary = %s
            WHERE id = %s
            """,
            (updated_preferences, user_summary, user_id),
        )
