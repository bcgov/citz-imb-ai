from ..models.feedback_model import QuestionResponse, FeedbackResponse


class FeedbackViews:
    @staticmethod
    def question_response(data: QuestionResponse) -> dict:
        """Format question submission response"""
        return data.dict()
    
    @staticmethod
    def feedback_response(data: FeedbackResponse) -> dict:
        """Format feedback response"""
        return data.dict()