from pydantic import BaseModel
from typing import List, Optional, Any


class QuestionSubmissionRequest(BaseModel):
    prompt: str


class FeedbackRequest(BaseModel):
    feedback: str
    index: str
    recording_id: str
    bulk: bool = False
    trulens_id: str = "unknown"


class RAGFeedbackRequest(BaseModel):
    feedback: str
    recording_id: str
    comment: Optional[str] = None
    trulens_id: str = "unknown"


class QuestionResponse(BaseModel):
    responses: List[Any]
    recording: str


class FeedbackResponse(BaseModel):
    status: bool
    rows: Optional[List[Any]] = None
    message: Optional[str] = None


class FetchFeedbackRequest(BaseModel):
    trulens_id: str = "unknown"