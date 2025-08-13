import json
from neo4j import GraphDatabase
import os
import random
from AzureSimple import AzureAI

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "admin"
NEO4J_PASSWORD = "admin"

db = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


# Azure Configuration
endpoint = os.getenv("AZURE_AI_ENDPOINT", "")
key = os.getenv("AZURE_AI_KEY", "")
azure = AzureAI(endpoint, key)

document_map = {}


def generate_question():
    with db.session() as session:
        if len(document_map.keys()) == 0:
            # Get all unique document titles from v3 label
            query = """
            MATCH (n:v3)
            WHERE n.document_title IS NOT NULL AND n.section_number IS NOT NULL
            WITH n.document_title AS title, COLLECT(DISTINCT n.section_number) AS sections
            RETURN title, sections
            ORDER BY title
            """
            result = session.run(query)
            for record in result:
                document_map[record["title"]] = record["sections"]
        # Select a random document and section from the map

        title = random.choice(list(document_map.keys()))
        sections = document_map[title]
        section = random.choice(sections)
        print(f"Selected document: {title}, section: {section}")
        # Retrieve all nodes related to the selected document and section
        query = """
        MATCH (n:v3)
        WHERE n.document_title = $title AND n.section_number = $section
        RETURN n
        """
        result = session.run(query, title=title, section=section)
        nodes = [record["n"] for record in result]

        prompt = f"""
        Your job is to create questions based the following context from a database of BC Laws.
        The context represents one section of an Act or Regulation, broken up into smaller pieces.
        Use the context to generate a question that could be asked about this section.
        
        The question should fall into one or many of the following categories:
        semantic: questions that require a vector similarity search to find relevant information
        explicit: questions that a neo4j cypher query can provide context for
        global: questions that require a broader understanding of the legal domain and may involve multiple documents or sections

        Here are some examples of questions and their categories:
        - "How much notice does a tenant have to give before terminating a tenancy?" (semantic) This question requires a vector search to find relevant information about tenancy laws.
        - "Do I need to wear a seatbelt in BC?" (semantic) This question requires a vector search to find relevant information about seatbelt laws.
        - "How many subsections are in this act?" (explicit) A cypher query could return the number of unique subsections.
        - "Give me a summary of the Motor Vehicle Act." (explicit) A cypher query would return the entire act for summarization.
        - "Which acts contain information about the rights of tenants in BC?" (global) This question requires a broader understanding of the legal domain and may involve multiple documents or sections.

        Your output should be a JSON object with the following structure:
        {{
            "question": "The question you generated",
            "category": ["semantic", "explicit", "global"]
        }}
        The category field may contain one or more of the categories listed above.
        Do not return any other fields or information.
        Do not wrap this json in a string or any other format.
        Do not return markdown or any other formatting.

        Context:
        {nodes}
        """
        # Run the Azure query to generate a question
        response = azure.call(prompt)
        if response:
            content = response.get("message", {}).get("content", "")
            print(f"Azure response content: {content}")
            if content:
                # Parse the response to extract the question and category
                try:
                    data = json.loads(content)
                    question = data.get("question", "")
                    category = data.get("category", [])
                    return {"question": question, "category": category}
                except json.JSONDecodeError:
                    pass


number_of_questions_per_file = 100
total_questions_desired = 10000

for i in range(total_questions_desired // number_of_questions_per_file):
    # How many generated_questions files already exist?
    existing_files = [f for f in os.listdir("./generated_questions")]
    new_file_index = len(existing_files) + 1
    # Pad the index with leading zeros to match the format (length 4)
    new_file_index_str = str(new_file_index).zfill(4)
    print(f"Creating file: {new_file_index_str}.jsonl")
    # Create the new filename
    output_file = f"./generated_questions/{new_file_index_str}.jsonl"
    # Write to jsonl file
    with open(output_file, "w") as f:
        for i in range(number_of_questions_per_file):
            print(
                f"Generating question {i + 1} of {number_of_questions_per_file}. File: {new_file_index_str}.jsonl"
            )
            question = generate_question()
            if question:
                print(f"Generated question: {question}")
                f.write(json.dumps(question) + "\n")
            else:
                print("No question generated.")
