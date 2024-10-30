from validate_json_output import validate_json_response
import json 

def model_response(question, raw_response):
    response = None
    try:
        # Get raw response
        #raw_response = get_response(AI_agent_prompt + question)

        # Validate JSON
        is_valid, message, json_data = validate_json_response(raw_response)

        if is_valid:
            # If valid, return the original JSON string
            responses = raw_response
        else:
            # If invalid, return an error message in JSON format
            error_response = json.dumps({
                "thought": "Error in response validation",
                "actions": [{
                    "action_type": "error_handling",
                    "priority": 1,
                    "action_params": {
                        "query": question,
                        "search_type": "none",
                        "function": "none",
                        "cypher": None,
                        "node_type": "none",
                        "is_regulation": False,
                        "keywords": None,
                        "error": message
                    }
                }],
                "confidence": 0.0,
                "requires_combination": False
            })
            responses = str(json_data)

    except Exception as e:
        # Handle any other errors with JSON response
        error_response = json.dumps({
            "thought": "Error in response processing",
            "actions": [{
                "action_type": "error_handling",
                "priority": 1,
                "action_params": {
                    "query": question,
                    "search_type": "none",
                    "function": "none",
                    "cypher": None,
                    "node_type": "none",
                    "is_regulation": False,
                    "keywords": None,
                    "error": str(e)
                }
            }],
            "confidence": 0.0,
            "requires_combination": False
        })
        responses = error_response
    
    return responses