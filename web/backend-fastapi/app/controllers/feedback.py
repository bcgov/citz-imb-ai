from fastapi import APIRouter, Form
from app.dependencies import get_user_info
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models import neo4j, trulens, topK
import json

router = APIRouter()

kg = None
tru = None
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

@router.post("/submit/")
async def submit_question(prompt: str = Form(...)):
    # Add appropriate imports

    # Global variables initialization
    global kg, tru, APP_ID, embeddings
    rag = topK.get_top_k()
    if kg is None:
        kg = neo4j.neo4j()
    if tru is None:
        tru = trulens.connect_trulens()
    tru_rag = trulens.tru_rag(rag)
    print(tru_rag)
    with tru_rag as recording:
        responses = rag.query(prompt, embeddings, kg)
    record = recording.get()
    print(responses)
    # Process question prompt
    return {"responses": responses, "recording": record.record_id}


@router.post("/feedback/")
async def feedback(
    feedback: str = Form(...),
    index: str = Form(...),
    recording_id: str = Form(...),
    bulk: bool = Form(False),
):
    # Add appropriate imports

    # Global variables initialization
    global tru, APP_ID
    if tru is None:
        tru = trulens.connect_trulens()

    # Process feedback
    rows = process_feedback(index, feedback, recording_id, bulk)
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}


@router.get("/fetch_feedback/")
async def fetch_all_feedback():
    # Add appropriate imports

    # Global variables initialization
    global tru, APP_ID
    if tru is None:
        tru = trulens.connect_trulens()

    # Fetch all feedback
    rows = trulens.fetch_all_feedback()
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}


def process_feedback(index, feedback, record_id=None, bulk=False):
    if bulk:
        multi_result = {"bulk": []}
        print(f"Feedback for Response: is {feedback} in bulk")
        feedback = feedback.split(",")
        for feedback_value in feedback:
            multi_result["bulk"].append(trulens.get_feedback_value(feedback_value))
        print(multi_result)
        multi_result = json.dumps(multi_result)
    else:
        print(f"Feedback for Response {index}: is {feedback}")
        feedbackvalue = trulens.get_feedback_value(feedback)
        multi_result = json.dumps({index: [feedbackvalue]})

    print(multi_result)

    tru_feedback = tru.add_feedback(
        name="Human Feedack",
        record_id=record_id,
        app_id=trulens.APP_ID,
        result=0,
        multi_result=multi_result,
    )
    print(record_id)
    print(tru_feedback)
    rows = trulens.fetch_human_feedback(record_id)
    if rows:
        return rows
    else:
        return None
