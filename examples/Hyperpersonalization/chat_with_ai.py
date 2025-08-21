# A simple test script to chat with an AI using Azure OpenAI
# This script connects to Azure OpenAI, retrieves user information from a local Postgres database,
# and allows the user to chat with the AI, storing the conversation in the database.
# The key takeaway is using the database to maintain context and history of the conversation, then summarizing it at the end.

from AzureSimple import AzureAI
import uuid
from datetime import datetime, timezone
import json
import os
import psycopg
from psycopg.rows import dict_row

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
        # If this user doesn't exist, add them to the user table
        if my_user is None:
            db.execute(
                f"""
                INSERT INTO "user" (id)
                VALUES ('{user_id}')
                RETURNING *
                """
            )
            my_user = db.fetchone()
            print("User inserted")
        else:
            print("User found")
        print(my_user)

        # Add user's info to the chat chain
        user_summary = (my_user["summary"] or "").strip()
        user_context_chat_obj = {
            "role": "system",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": (
                f"Here is some infor about the user: {user_summary}"
                if user_summary
                else "No user summary provided."
            ),
        }
        # Start Chat with AI
        chat_id = str(uuid.uuid4())  # Random identifier
        print("Starting chat with AI. Type 'bye' to stop.")
        user_input = input("User: ")
        is_first_input = True
        # Now, let's continue the chat with the AI, continuously adding to the chat chain.
        while user_input != "bye":
            user_chat_obj = {
                "role": "user",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content": user_input,
            }
            if is_first_input:
                # New chat entry must be inserted
                db.execute(
                    """
                    INSERT INTO chat (id, user_id, created_at, is_active)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (chat_id, user_id, datetime.now(timezone.utc).isoformat(), True),
                )
                is_first_input = False
                # Start chat chain with user's prompt
                chat_chain = [user_chat_obj]
            else:
                # Get existing chat and update chat_chain
                db.execute(
                    """
                    SELECT chat_chain FROM chat
                    WHERE id = %s
                    """,
                    (chat_id,),
                )
                chat_entry = db.fetchone()
                chat_chain = (
                    chat_entry["chat_chain"]
                    if chat_entry and chat_entry["chat_chain"]
                    else []
                )
                chat_chain.append(user_chat_obj)

            # Add user info to the front of the chat chain
            # We do this so the AI has context on who the user is
            # but we don't want to save this user info in the chat history
            chain_with_user_info = [user_context_chat_obj] + chat_chain

            # Send the message to the AI
            response = azure.call(chain_with_user_info)
            print("AI:", response.get("message", {}).get("content", ""))
            # Add its response to the chat chain
            ai_chat_obj = {
                "role": "assistant",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content": response.get("message", {}).get("content", ""),
            }
            chat_chain.append(ai_chat_obj)
            # Update the chat entry in the database
            db.execute(
                """
                UPDATE chat
                SET chat_chain = %s
                WHERE id = %s
                """,
                (json.dumps(chat_chain), chat_id),
            )

            # Get new user input
            user_input = input("User: ")
        print("Chat ended.\n")

        # This chat is over, so let's mark it as inactive and summarize it.
        summary_prompt = (
            "Summarize the following chat. Keep this summary concise.\n"
            + json.dumps(chat_chain, indent=2)
        )
        summary = azure.call([{"role": "system", "content": summary_prompt}])
        summary_content = summary.get("message", {}).get("content", "")
        print("Summary:", summary_content)
        db.execute(
            """
            UPDATE chat
            SET is_active = FALSE, summary = %s
            WHERE id = %s
            """,
            (summary_content, chat_id),
        )
        # Normally, you would clear the original chat chain from the database
        # but for this example, we keep it for reference.
        # You would also probably keep this chat alive for a set period of time
        # before this occurs. Maybe summarize more regularly until then.
