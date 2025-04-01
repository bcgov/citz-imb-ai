from fastapi import APIRouter, Form
from app.models import trulens, rag, neo4j
from langchain_community.embeddings import HuggingFaceEmbeddings
import logging

router = APIRouter()

kg = None
tru = None
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


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
        responses = rag_fn.query(prompt, None, embeddings, kg)
    record = recording.get()
    # Process question prompt
    return {"responses": responses, "recording": record.record_id}


@router.post("/feedback/")
async def feedback(
    feedback: str = Form(...),
    index: str = Form(...),
    recording_id: str = Form(...),
    bulk: bool = Form(False),
    trulens_id: str = Form("unknown"),
):
    # Global variables initialization
    global tru
    if tru is None:
        tru = trulens.connect_trulens()

    # Process feedback
    rows = trulens.process_feedback(tru, index, feedback, recording_id, bulk)
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}


@router.post("/feedbackrag/")
async def feedbackrag(
    feedback: str = Form(...),
    recording_id: str = Form(...),
    comment: str = Form(None),
    trulens_id: str = Form("unknown"),
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
