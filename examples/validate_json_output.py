import json
from typing import List, Dict, Any

def validate_json_response(output: str) -> tuple[bool, str, Dict[str, Any]]:
    """Validates that the output is proper JSON and has required fields"""
    try:
        # Try to parse JSON
        json_data = json.loads(output)
        
        # Check required fields
        required_fields = ["thought", "actions", "confidence", "requires_combination"]
        for field in required_fields:
            if field not in json_data:
                return False, f"Missing required field: {field}", {}
        
        # Validate actions structure
        if not isinstance(json_data["actions"], list):
            return False, "Actions must be a list", {}
        
        for action in json_data["actions"]:
            # Check required action fields
            action_fields = ["action_type", "priority", "action_params"]
            for field in action_fields:
                if field not in action:
                    return False, f"Action missing required field: {field}", {}
            
            # Validate action_type
            valid_action_types = {
                "semantic_search", "explicit_search", "graph_search",
                "community_detection", "count_keywords"
            }
            if action["action_type"] not in valid_action_types:
                return False, f"Invalid action_type: {action['action_type']}", {}
            
            # Validate priority
            if not isinstance(action["priority"], int) or not 1 <= action["priority"] <= 5:
                return False, "Priority must be integer between 1 and 5", {}
            
            # Validate action_params
            required_params = ["query", "search_type", "function", "cypher", "node_type"]
            for param in required_params:
                if param not in action["action_params"]:
                    return False, f"Action params missing: {param}", {}
        
        # Validate confidence score
        if not isinstance(json_data["confidence"], (int, float)) or not 0 <= json_data["confidence"] <= 1:
            return False, "Confidence must be float between 0 and 1", {}
        
        # Validate requires_combination
        if not isinstance(json_data["requires_combination"], bool):
            return False, "requires_combination must be boolean", {}
            
        return True, "Valid", json_data
        
    except json.JSONDecodeError:
        return False, "Invalid JSON format", {}
    except Exception as e:
        return False, f"Validation error: {str(e)}", {}