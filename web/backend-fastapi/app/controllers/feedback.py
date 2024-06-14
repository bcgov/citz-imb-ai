from fastapi import APIRouter, Form
from app.dependencies import get_user_info
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.models import neo4j, trulens, rag, run_onnx
import json

router = APIRouter()

kg = None
tru = None
#embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embeddings = run_onnx

@router.post("/submit/")
async def submit_question(prompt: str = Form(...)):
    # Add appropriate imports

    # Global variables initialization
    global kg, tru, APP_ID, embeddings
    rag_fn = rag.get_top_k()
    if kg is None:
        kg = neo4j.neo4j()
    if tru is None:
        tru = trulens.connect_trulens()
    tru_rag = trulens.tru_rag(rag_fn)
    with tru_rag as recording:
        responses = rag_fn.query(prompt, embeddings, kg)
    record = recording.get()
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
        multi_result = json.dumps(multi_result)
    else:
        feedbackvalue = trulens.get_feedback_value(feedback)
        multi_result = json.dumps({index: [feedbackvalue]})

    tru_feedback = tru.add_feedback(
        name="Human Feedack",
        record_id=record_id,
        app_id=trulens.APP_ID,
        result=0,
        multi_result=multi_result,
    )
    rows = trulens.fetch_human_feedback(record_id)
    if rows:
        return rows
    else:
        return None