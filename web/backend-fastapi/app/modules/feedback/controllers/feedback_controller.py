from fastapi import APIRouter, Form
from ..services.feedback_service import FeedbackService
from ..views.feedback_views import FeedbackViews
from ..models.feedback_model import (
    QuestionSubmissionRequest,
    FeedbackRequest,
    RAGFeedbackRequest,
    FetchFeedbackRequest
)


class FeedbackController:
    def __init__(self):
        self.router = APIRouter()
        self.feedback_service = FeedbackService()
        self.feedback_views = FeedbackViews()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all feedback routes"""
        
        @self.router.post("/submit/")
        async def submit_question(prompt: str = Form(...)):
            request = QuestionSubmissionRequest(prompt=prompt)
            result = await self.feedback_service.submit_question(request)
            return self.feedback_views.question_response(result)
        
        @self.router.post("/feedback/")
        async def feedback(
            feedback: str = Form(...),
            index: str = Form(...),
            recording_id: str = Form(...),
            bulk: bool = Form(False),
            trulens_id: str = Form("unknown"),
        ):
            request = FeedbackRequest(
                feedback=feedback,
                index=index,
                recording_id=recording_id,
                bulk=bulk,
                trulens_id=trulens_id
            )
            result = await self.feedback_service.process_feedback(request)
            return self.feedback_views.feedback_response(result)
        
        @self.router.post("/feedbackrag/")
        async def feedbackrag(
            feedback: str = Form(...),
            recording_id: str = Form(...),
            comment: str = Form(None),
            trulens_id: str = Form("unknown"),
        ):
            request = RAGFeedbackRequest(
                feedback=feedback,
                recording_id=recording_id,
                comment=comment,
                trulens_id=trulens_id
            )
            result = await self.feedback_service.process_rag_feedback(request)
            return self.feedback_views.feedback_response(result)
        
        @self.router.get("/fetch_feedback/")
        async def fetch_all_feedback(trulens_id: str = "unknown"):
            request = FetchFeedbackRequest(trulens_id=trulens_id)
            result = await self.feedback_service.fetch_all_feedback(request)
            return self.feedback_views.feedback_response(result)


# Create router instance
feedback_controller = FeedbackController()
router = feedback_controller.router