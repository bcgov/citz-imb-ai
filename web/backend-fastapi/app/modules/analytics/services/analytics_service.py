import os
import json
import aiofiles
import asyncio
from typing import List, Dict, Any

# AnalyticsService class to handle analytics data
class AnalyticsService:
    # initialize the service
    def __init__(self):
        self.file_path = os.path.join("analytics_data", "all_analytics.json")
        self.lock = asyncio.Lock()
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
        # Create the file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    # read data from disk
    async def read_data(self) -> List[Dict[str, Any]]:
        async with aiofiles.open(self.file_path, mode='r') as file:
            content = await file.read()
            if not content:
                return []
            
            data = json.loads(content)
            # Handle case where file contains a dict instead of list
            if isinstance(data, dict):
                return []
            return data if isinstance(data, list) else []

    # write data to disk
    async def write_data(self, data: List[Dict[str, Any]]):
        async with aiofiles.open(self.file_path, mode='w') as file:
            await file.write(json.dumps(data, indent=2))

    # save analytics data
    async def save_analytics(self, analytics_data: Dict[str, Any]) -> str:
        session_id = analytics_data.get('sessionId')
        async with self.lock:
            all_data = await self.read_data()
            session_index = next((i for i, d in enumerate(all_data) if d["sessionId"] == session_id), None)
            if session_index is not None:
                all_data[session_index] = analytics_data
            else:
                all_data.append(analytics_data)
            await self.write_data(all_data)
        return f"Analytics data saved successfully for session {session_id}"

    # update analytics data
    async def update_analytics(self, updates: List[Dict[str, Any]]) -> str:
        async with self.lock:
            all_data = await self.read_data()
            session_dict = {d["sessionId"]: d for d in all_data}
            for update in updates:
                session_id = update.get('sessionId')
                if session_id not in session_dict:
                    if 'newChat' in update:
                        new_session = {"sessionId": session_id, "chats": [update['newChat']]}
                        all_data.append(new_session)
                        session_dict[session_id] = new_session
                else:
                    session_data = session_dict[session_id]
                    
                    if 'newChat' in update:
                        session_data['chats'].append(update['newChat'])
                    
                    if 'sourceUpdate' in update:
                        source_update = update['sourceUpdate']
                        chat_index = source_update['chatIndex']
                        
                        # Find chat by matching chatIndex field in llmResponseInteraction
                        target_chat = None
                        for chat in session_data['chats']:
                            if chat.get('llmResponseInteraction', {}).get('chatIndex') == chat_index:
                                target_chat = chat
                                break
                        
                        if target_chat and 'sources' in target_chat:
                            source = next((s for s in target_chat['sources'] if s['sourceKey'] == source_update['sourceKey']), None)
                            if source:
                                source.update(source_update)
                    
                    if 'llmResponseUpdate' in update:
                        llm_update = update['llmResponseUpdate']
                        chat_index = llm_update['chatIndex']
                        
                        # Find chat by matching chatIndex field in llmResponseInteraction
                        target_chat = None
                        for chat in session_data['chats']:
                            if chat.get('llmResponseInteraction', {}).get('chatIndex') == chat_index:
                                target_chat = chat
                                break
                        
                        if target_chat and 'llmResponseInteraction' in target_chat:
                            target_chat['llmResponseInteraction'].update(llm_update)
            await self.write_data(all_data)
        return "Analytics data updated successfully"
