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

        # Define a single file for all analytics data
        file_path = os.path.join("analytics_data", "all_analytics.json")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read existing data or create an empty list
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                all_data = json.load(file)
        else:
            all_data = []

        # Check if session_id already exists
        session_index = next((index for (index, d) in enumerate(all_data) if d["sessionId"] == session_id), None)

        if session_index is not None:
            # Update existing session data
            all_data[session_index] = analytics_data
        else:
            # Add new session data
            all_data.append(analytics_data)

        # Write the updated data back to the file
        with open(file_path, "w") as file:
            json.dump(all_data, file, indent=2)

        return {"message": f"Analytics data saved successfully for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
