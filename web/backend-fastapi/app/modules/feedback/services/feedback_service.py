import logging
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.shared.models import trulens, rag, neo4j
from ..models.feedback_model import (
    QuestionSubmissionRequest,
    FeedbackRequest,
    RAGFeedbackRequest,
    QuestionResponse,
    FeedbackResponse,
    FetchFeedbackRequest
)


class FeedbackService:
    def __init__(self):
        self.kg = None
        self.tru = None
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    def _initialize_components(self):
        """Initialize knowledge graph and trulens if not already done"""
        if self.kg is None:
            self.kg = neo4j.neo4j()
        if self.tru is None:
            self.tru = trulens.connect_trulens()
    
    async def submit_question(self, request: QuestionSubmissionRequest) -> QuestionResponse:
        """Submit a question and get response"""
        self._initialize_components()
        
        rag_fn = rag.get_top_k()
        tru_rag = trulens.tru_rag(rag_fn)
        
        with tru_rag as recording:
            responses = rag_fn.query(request.prompt, None, self.embeddings, self.kg)
        
        record = recording.get()
        return QuestionResponse(responses=responses, recording=record.record_id)
    
    async def process_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        """Process user feedback"""
        self._initialize_components()
        
        rows = trulens.process_feedback(
            self.tru, 
            request.trulens_id, 
            request.index, 
            request.feedback, 
            request.recording_id, 
            request.bulk
        )
        
        if rows:
            return FeedbackResponse(status=True, rows=rows)
        else:
            return FeedbackResponse(status=False)
    
    async def process_rag_feedback(self, request: RAGFeedbackRequest) -> FeedbackResponse:
        """Process RAG-specific feedback"""
        self._initialize_components()
        
        try:
            rows = trulens.process_rag_feedback(
                request.feedback, 
                request.trulens_id, 
                request.recording_id, 
                self.tru, 
                request.comment
            )
            
            if rows:
                return FeedbackResponse(
                    status=True,
                    message="Feedback submitted successfully",
                    rows=rows
                )
            
            return FeedbackResponse(
                status=False, 
                message="No feedback data found"
            )
        
        except Exception as e:
            logging.error(f"Error processing feedback: {str(e)}")
            return FeedbackResponse(
                status=False,
                message="An internal error has occurred. Please try again later."
            )
    
    async def fetch_all_feedback(self, request: FetchFeedbackRequest) -> FeedbackResponse:
        """Fetch all feedback for a given trulens_id"""
        self._initialize_components()
        
        rows = trulens.fetch_all_feedback(request.trulens_id)
        
        if rows:
            return FeedbackResponse(status=True, rows=rows)
        else:
            return FeedbackResponse(status=False)