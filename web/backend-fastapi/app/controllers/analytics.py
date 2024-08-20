from fastapi import APIRouter, Request, HTTPException
import os
import json
from typing import List, Dict, Any
import aiofiles
import asyncio

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
        
        file_path = os.path.join("analytics_data", "all_analytics.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        async with aiofiles.open(file_path, mode='r+') as file:
            content = await file.read()
            all_data = json.loads(content) if content else []

            # Create a dictionary for faster session lookup
            session_dict = {d["sessionId"]: d for d in all_data}

            for update in updates:
                session_id = update.get('sessionId')
                if not session_id:
                    raise HTTPException(status_code=400, detail="sessionId is required in the update data")

                if session_id not in session_dict:
                    if 'newChat' in update:
                        new_session = {"sessionId": session_id, "chats": [update['newChat']]}
                        all_data.append(new_session)
                        session_dict[session_id] = new_session
                    else:
                        raise HTTPException(status_code=400, detail=f"Session {session_id} not found")
                else:
                    session_data = session_dict[session_id]
                    
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

            await file.seek(0)
            await file.write(json.dumps(all_data, indent=2))
            await file.truncate()

        return {"message": "Analytics data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
