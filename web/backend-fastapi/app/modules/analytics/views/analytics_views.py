from ..models.analytics_model import AnalyticsResponse


class AnalyticsViews:
    @staticmethod
    def analytics_response(message: str) -> dict:
        """Format analytics response"""
        return AnalyticsResponse(message=message).dict()
    
    @staticmethod
    def error_response(error: str) -> dict:
        """Format error response"""
        return AnalyticsResponse(message=error, status="error").dict()