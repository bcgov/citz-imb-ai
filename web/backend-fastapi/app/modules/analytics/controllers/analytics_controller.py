from fastapi import APIRouter, Request, HTTPException
from ..services.analytics_service import AnalyticsService
from ..views.analytics_views import AnalyticsViews


class AnalyticsController:
    def __init__(self):
        self.router = APIRouter()
        self.analytics_service = AnalyticsService()
        self.analytics_views = AnalyticsViews()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all analytics routes"""
        
        @self.router.post("/saveAnalytics")
        async def save_analytics(request: Request):
            try:
                analytics_data = await request.json()
                session_id = analytics_data.get('sessionId')
                
                if not session_id:
                    raise HTTPException(
                        status_code=400, 
                        detail="sessionId is required in the analytics data"
                    )
                
                message = await self.analytics_service.save_analytics(analytics_data)
                return self.analytics_views.analytics_response(message)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.patch("/updateAnalytics")
        async def update_analytics(request: Request):
            try:
                updates = await request.json()
                message = await self.analytics_service.update_analytics(updates)
                return self.analytics_views.analytics_response(message)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


# Create router instance
analytics_controller = AnalyticsController()
router = analytics_controller.router