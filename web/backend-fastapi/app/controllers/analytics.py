from fastapi import APIRouter, Request, HTTPException
import os
import json

router = APIRouter()

@router.post("/saveAnalytics")
async def save_analytics(request: Request):
    try:
        analytics_data = await request.json()
        file_path = os.path.join("analytics_data", "analyticsData.json")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the analytics data to a JSON file
        with open(file_path, "w") as file:
            json.dump(analytics_data, file, indent=2)

        return {"message": "Analytics data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
