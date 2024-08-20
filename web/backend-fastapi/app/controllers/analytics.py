from fastapi import APIRouter, Request, HTTPException
import os
import json
from typing import List, Dict, Any

router = APIRouter()

@router.post("/saveAnalytics")
async def save_analytics(request: Request):
    try:
        analytics_data = await request.json()
        
        # Extract sessionId from the analytics_data
        session_id = analytics_data.get('sessionId')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="sessionId is required in the analytics data")

        # Define file path for all analytics data
        file_path = os.path.join("analytics_data", "all_analytics.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read existing data or create an empty list
        all_data = json.load(open(file_path, "r")) if os.path.exists(file_path) else []

        # Update existing session or add new session data
        session_index = next((i for i, d in enumerate(all_data) if d["sessionId"] == session_id), None)
        if session_index is not None:
            all_data[session_index] = analytics_data
        else:
            all_data.append(analytics_data)

        # Write updated data back to file
        with open(file_path, "w") as file:
            json.dump(all_data, file, indent=2)

        return {"message": f"Analytics data saved successfully for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/updateAnalytics")
async def update_analytics(request: Request):
    try:
        updates: List[Dict[str, Any]] = await request.json()
        
        # Define file path and ensure directory exists
        file_path = os.path.join("analytics_data", "all_analytics.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read existing data or create an empty list
        all_data = json.load(open(file_path, "r")) if os.path.exists(file_path) else []

        for update in updates:
            session_id = update.get('sessionId')
            if not session_id:
                raise HTTPException(status_code=400, detail="sessionId is required in the update data")

            # Find session index or create new session if 'newChat' is present
            session_index = next((i for i, d in enumerate(all_data) if d["sessionId"] == session_id), None)
            if session_index is None:
                if 'newChat' in update:
                    all_data.append({"sessionId": session_id, "chats": [update['newChat']]})
                else:
                    raise HTTPException(status_code=400, detail=f"Session {session_id} not found")
            else:
                session_data = all_data[session_index]
                
                # Handle different types of updates
                if 'newChat' in update:
                    session_data['chats'].append(update['newChat'])
                
                if 'sourceUpdate' in update:
                    source_update = update['sourceUpdate']
                    chat = session_data['chats'][source_update['chatIndex']]
                    source = next(s for s in chat['sources'] if s['sourceKey'] == source_update['sourceKey'])
                    source.update(source_update)
                
                if 'llmResponseUpdate' in update:
                    llm_update = update['llmResponseUpdate']
                    chat = session_data['chats'][llm_update['chatIndex']]
                    chat['llmResponseInteraction'].update(llm_update)

        # Write updated data back to file
        with open(file_path, "w") as file:
            json.dump(all_data, file, indent=2)

        return {"message": "Analytics data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
