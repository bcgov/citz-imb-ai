from fastapi import APIRouter, Form
from app.models import trulens
import json
import logging

router = APIRouter()

kg = None
tru = None


@router.post("/feedback/")
async def feedback(
    feedback: str = Form(...),
    index: str = Form(...),
    recording_id: str = Form(...),
    bulk: bool = Form(False),
    trulens_id: str = Form(...),
):
    # Global variables initialization
    global tru
    if tru is None:
        tru = trulens.connect_trulens()

    # Process feedback
    rows = process_feedback(
        index,
        feedback,
        trulens_id,
        recording_id,
        bulk,
    )
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}


@router.post("/feedbackrag/")
async def feedbackrag(
    feedback: str = Form(...),
    recording_id: str = Form(...),
    comment: str = Form(None),
    trulens_id: str = Form(...),
):
    global tru
    if tru is None:
        tru = trulens.connect_trulens()

    try:
        rows = trulens.process_rag_feedback(
            feedback, trulens_id, recording_id, tru, comment
        )
        if rows:
            return {
                "status": True,
                "message": "Feedback submitted successfully",
                "rows": rows,
            }
        return {"status": False, "message": "No feedback data found"}
    except Exception as e:
        logging.error(f"Error processing feedback: {str(e)}")
        return {
            "status": False,
            "message": "An internal error has occurred. Please try again later.",
        }


@router.get("/fetch_feedback/")
async def fetch_all_feedback(trulens_id: str = "unknown"):
    # Add appropriate imports

    # Global variables initialization
    global tru
    if tru is None:
        tru = trulens.connect_trulens()

    # Fetch all feedback
    rows = trulens.fetch_all_feedback(trulens_id)
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}


def process_feedback(index, feedback, trulens_id, record_id=None, bulk=False):
    if bulk:
        multi_result = {"bulk": []}
        feedback = feedback.split(",")
        for feedback_value in feedback:
            multi_result["bulk"].append(trulens.get_feedback_value(feedback_value))
        print(multi_result)
        multi_result = json.dumps(multi_result)
    else:
        feedbackvalue = trulens.get_feedback_value(feedback)
        multi_result = json.dumps({index: [feedbackvalue]})

    print(multi_result)

    tru_feedback = tru.add_feedback(
        name="Human Feedack",
        record_id=record_id,
        app_id=trulens_id,
        result=0,
        multi_result=multi_result,
    )
    rows = trulens.fetch_human_feedback(record_id)
    if rows:
        return rows
    else:
        return None
