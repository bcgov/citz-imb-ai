from fastapi import APIRouter, Request, HTTPException
from app.services.analytics_service import AnalyticsService

router = APIRouter()
analytics_service = AnalyticsService()

@router.post("/saveAnalytics")
async def save_analytics(request: Request):
    try:
        analytics_data = await request.json()
        session_id = analytics_data.get('sessionId')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="sessionId is required in the analytics data")
        
        message = await analytics_service.save_analytics(analytics_data)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/updateAnalytics")
async def update_analytics(request: Request):
    try:
        updates = await request.json()
        message = await analytics_service.update_analytics(updates)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
