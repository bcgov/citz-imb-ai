from fastapi import APIRouter, Request, HTTPException
import os
import json

router = APIRouter()

@router.post("/saveAnalytics")
async def save_analytics(request: Request):
    try:
        analytics_data = await request.json()
        
        # Extract sessionId from the analytics_data
        session_id = analytics_data.get('sessionId')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="sessionId is required in the analytics data")

        # Create a filename based on the sessionId
        file_name = f"analytics_{session_id}.json"
        file_path = os.path.join("analytics_data", file_name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the analytics data to a JSON file, overwriting if it exists
        with open(file_path, "w") as file:
            json.dump(analytics_data, file, indent=2)

        return {"message": f"Analytics data saved successfully for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
