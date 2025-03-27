import psycopg2
import os
from trulens_eval import Tru
from trulens_eval import TruCustomApp
import json


def connect_trulens():
    TRULENS_USER = os.getenv("TRULENS_USER")
    TRULENS_PASSWORD = os.getenv("TRULENS_PASSWORD")
    TRULENS_DB = os.getenv("TRULENS_DB")
    TRULENS_PORT = os.getenv("TRULENS_PORT")
    TRULENS_HOST = os.getenv("TRULENS_HOST")
    TRULENS_CONNECTION_STRING = f"postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}"
    tru = Tru(database_url=TRULENS_CONNECTION_STRING)
    return tru


def tru_connect():
    TRULENS_USER = os.getenv("TRULENS_USER")
    TRULENS_PASSWORD = os.getenv("TRULENS_PASSWORD")
    TRULENS_DB = os.getenv("TRULENS_DB")
    TRULENS_PORT = os.getenv("TRULENS_PORT")
    TRULENS_HOST = os.getenv("TRULENS_HOST")
    conn = psycopg2.connect(
        host=TRULENS_HOST,
        database=TRULENS_DB,
        user=TRULENS_USER,
        password=TRULENS_PASSWORD,
    )
    return conn


def fetch_rag_feedback(record_id):
    conn = tru_connect()
    cur = conn.cursor()  # creating a cursor
    cur.execute(
        """
        SELECT R.input, F.result, F.result, R.app_id result FROM public.records R 
        LEFT JOIN feedbacks F ON F.record_id = R.record_id WHERE
        R.record_id= %s
    """,
        (record_id,),
    )
    rows = cur.fetchall()
    return rows


def fetch_human_feedback(record_id):
    conn = tru_connect()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 
                R.input,
                F.multi_result,
                F.result,
                R.app_id
            FROM public.records R 
            LEFT JOIN feedbacks F ON F.record_id = R.record_id 
            WHERE R.record_id = %s
            """,
            (record_id,),
        )
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()


def get_feedback_value(feedback):
    if feedback == "up_vote":
        return 1
    elif feedback == "down_vote":
        return -1
    else:  # no_vote
        return 0


def process_rag_feedback(feedback, trulens_id, record_id=None, tru=None, comment=None):
    feedback_value = int(get_feedback_value(feedback))

    feedback_data = {
        "name": "Human Feedback",
        "record_id": record_id,
        "app_id": trulens_id,
        "result": feedback_value,
    }

    # Add comment to multi_result if provided
    if comment:
        feedback_data["multi_result"] = json.dumps(
            {"comment": comment, "vote_type": feedback}  # Store the original vote type
        )

    tru_feedback = tru.add_feedback(**feedback_data)

    rows = fetch_human_feedback(record_id)
    return rows if rows else None


def tru_rag(rag, trulens_id):
    return TruCustomApp(rag, app_id=trulens_id)


def fetch_all_feedback(trulens_id):
    conn = tru_connect()
    cur = conn.cursor()  # creating a cursor
    cur.execute(
        """SELECT R.input, R.record_json as record_json, F.multi_result, F.result, R.app_id result FROM public.records R 
    LEFT Join feedbacks F ON F.record_id = R.record_id WHERE
    R.app_id = %s""",
        (trulens_id),
    )
    rows = cur.fetchall()
    return rows
