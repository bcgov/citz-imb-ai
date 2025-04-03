import psycopg2
import os
from trulens.apps.app import instrument
from trulens.core import TruSession
from trulens.core.database.connector.default import DefaultDBConnector
from trulens.core.schema.feedback import FeedbackCall
from trulens.apps.app import TruApp
import json

APP_VERSION = "3"


def connect_trulens():
    TRULENS_USER = os.getenv("TRULENS_USER")
    TRULENS_PASSWORD = os.getenv("TRULENS_PASSWORD")
    TRULENS_DB = os.getenv("TRULENS_DB")
    TRULENS_PORT = os.getenv("TRULENS_PORT")
    TRULENS_HOST = os.getenv("TRULENS_HOST")
    TRULENS_CONNECTION_STRING = f"postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}"
    connector = DefaultDBConnector(database_url=TRULENS_CONNECTION_STRING)
    session = TruSession(connector=connector)
    return session


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
            FROM public.trulens_records R 
            LEFT JOIN trulens_feedbacks F ON F.record_id = R.record_id 
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


def process_feedback(tru, trulens_id, index, feedback, record_id=None, bulk=False):
    if bulk:
        multi_result = {"bulk": []}
        feedback = feedback.split(",")
        for feedback_value in feedback:
            multi_result["bulk"].append(int(get_feedback_value(feedback_value)))
        multi_result = json.dumps(multi_result)
    else:
        feedbackvalue = int(get_feedback_value(feedback))
        multi_result = json.dumps({index: [feedbackvalue]})

    tru_feedback = tru.add_feedback(
        name="Human Feedack",
        record_id=record_id,
        app_id=trulens_id,
        result=0,
        multi_result=multi_result,
    )
    rows = fetch_human_feedback(record_id)
    if rows:
        return rows
    else:
        return None


def process_rag_feedback(feedback, trulens_id, record_id=None, tru=None, comment=None):
    feedback_value = int(get_feedback_value(feedback))

    if comment is None:
        comment = "No comments provided"

    calls = []
    calls.append(FeedbackCall(args={}, ret=feedback_value, meta={"reason": comment}))

    tru.add_feedback(
        name="Human Feedback",
        record_id=record_id,
        app_id=trulens_id,
        result=feedback_value,
        calls=calls,
    )
    print(tru)

    rows = fetch_human_feedback(record_id)
    return rows if rows else None


def tru_rag(rag, trulens_id):
    return TruApp(rag, app_id=trulens_id, app_version=APP_VERSION)


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
