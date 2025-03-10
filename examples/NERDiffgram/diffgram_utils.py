from diffgram import Project
import requests
import json

def get_schema_list(id, project, DIFFGRAM_CONFIG):
    auth = project.session.auth
    url = f"{DIFFGRAM_CONFIG['host']}/api/project/{DIFFGRAM_CONFIG['project_string_id']}/labels?schema_id={id}"
    # Step 4: Make the POST request using the SDK's session auth
    response = requests.get(url, auth=auth)
    # Step 5: Handle the response
    if response.status_code == 200:
        #print("Annotation update successful!")
        #pprint.pprint(response.json())  # View the updated data
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)  # Print error details for debugging


def find_schema(schema_name, project):
    schema_id = None

    # List the existing schemas in your Diffgram project.
    schemas = project.schema.list()
    print("Existing Schemas in Diffgram:")
    print(json.dumps(schemas, indent=2))
    
    # Check if a schema with the name NER_schema_name already exists.
    for schema in schemas:
        if schema.get('name') == schema_name:
            schema_id = schema.get('id')
            break
    
    # If the schema does not exist, create a new one.
    if schema_id is None:
        print(f"Schema '{schema_name}' not found. Creating a new one...")
        json_response = project.new_schema(name=schema_name)
        schema_id = json_response.get("id")
        print(f"Created new schema with id: {schema_id}")
    else:
        print(f"Schema '{schema_name}' already exists with id: {schema_id}")
    return schema_id

def get_all_tasks(project, get_job):
    jobs_with_data_index = []
    for job_key, job_list in enumerate(get_job):
        try:
            nickname = job_list['attached_directories_dict']['attached_directories_list'][0]['nickname']
            if nickname:
                job_value = {}
                job_value['nickname'] = nickname
                job_value['index'] = job_key
                jobs_with_data_index.append(job_value)
            #print(nickname)
        except KeyError:
            print("Key not found.")
        except IndexError:
            print("List index out of range.")
    return jobs_with_data_index

def get_diffgram_task_url(job_id, file_id, auth, DIFFGRAM_CONFIG):
    """
    Fetches the task URL for a given job ID and file ID in Diffgram.
    Parameters:
        job_id (int): The job ID.
        file_id (int): The file ID.
        auth (object): Diffgram session authentication.
    Returns:
        str: The URL to the annotation task, or None if not found.
    """
    url = f"{DIFFGRAM_CONFIG['host']}/api/v1/job/{job_id}/task/list"
    data = {"page_number": 0, "job_id": str(job_id), "mode_data": "direct_route", "status": "all", "limit_count": 32}
    response = requests.post(url, json=data, auth=auth)
    if response.status_code == 200:
        for task in response.json().get("task_list", []):
            if int(task["file"]["id"]) == int(file_id):
                return f"{DIFFGRAM_CONFIG['host']}/task/{task['id']}?file={file_id}&"
    return None