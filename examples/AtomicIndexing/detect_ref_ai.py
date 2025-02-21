# If using bedrock for initial processing
import boto3
from botocore.config import Config
import os
import json
from neo4j_functions import (
    find_node,
    get_ref_edge,
    create_edge,
    update_edge_weight,
    get_whole_tree,
)

# Standard Bedrock session setup
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Default retry mode is legacy otherwise
config = Config(retries={"max_attempts": 3, "mode": "standard"})
bedrock_runtime = session.client(
    "bedrock-runtime", region_name="us-east-1", config=config
)


# Standard kwargs for claude
def get_claude_kwargs(prompt):
    kwargs = {
        "modelId": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 5000,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
            }
        ),
    }
    return kwargs


# Usual wrapper function for bedrock call
def get_agent_response(prompt):
    kwargs = get_claude_kwargs(prompt)
    response = bedrock_runtime.invoke_model(**kwargs)
    response_body = json.loads(response.get("body").read())
    return response_body["content"][0]["text"]


# Creates a text prompt for the LLM. Inserts the text that the LLM should parse for references.
def build_prompt(insert_text):
    prompt_base = f"""
    Your job is to identify references in BC laws and give back these references in a structured format.
    The format should be a list of JSON objects with the following schema:
    {{
      "section": "string",
      "subsection": "string",
      "paragraph": "string",
      "subparagraph": "string",
      "act": "string",
      "count": number
    }}
    Do not return any other text apart from this JSON.

    It is not guaranteed that all these fields will be in the provided text. If they cannot be determined, the value should be a blank string.
    Sections are always numbers, sometimes with a decimal. They immediately follow the word "section".
    Subsections are always numbers, sometimes with a decimal. They immediately follow the word "subsection" but also can be enclosed in parentheses like here: "section 1 (2)" where 2 is the subsection.
    Paragraphs are always letters enclosed in parentheses. In "section 1 (a)", a is the paragraph.
    Subparagraphs are always Roman numerals enclosed on parentheses. In "subsection 1 (a)(iv)", "iv" is the subparagraph.
    Some texts will have references from other acts. These will use the text "of the _____ Act", with the blank space being the name of the act. Put this name in the "act" property with the word Act after.
    Some texts will have use the words "of this Act" after a reference. In this case, add the property "this_act" with a boolean value of true.
    If there are two objects with the exact same properties, increase the count property. The count property should equal the number of times that reference occurs in the text.

    Here are a few examples:
    Input: "section 8" Output: [{{"section": "8", "count": 1}}]
    Input: "sections 5 and 6" Output: [{{"section": "5", "count": 1}}, {{"section": "6", "count": 1}}]
    Input: "section 3 (4)" Output: [{{"section": "3", "subsection": "4", "count": 1}}]
    Input: "section 1 (2)(a)(iii)" Output: [{{"section": "1", "subsection": "2", "paragraph": "a", "subparagraph": "iii", "count": 1}}]
    Input: "subsection 3" Output: [{{"subsection": "3", "count": 1}}]
    Input: "subsection (4)(a)" Output: [{{"subsection": "4", "paragraph": "a", "count": 1}}]
    Input: "subsections (2) and (3)" Output: [{{"subsection": "2", "count": 1}}, {{"subsection": "3", "count": 1}}]
    Input: "subsections ( 2 ) and ( 3 )" Output: [{{"subsection": "2", "count": 1}}, {{"subsection": "3", "count": 1}}]
    Input: "section 8 of the Property Act" Output: [{{"section": "8", "act": "Property Act", "count": 1}}]
    Input: "section 3 of this Act" Output: [{{"section": "3", "this_act": true, "count": 1}}]

    Please find the correct output for this text:
    {insert_text}
    """
    return prompt_base


#
# Node provided for this function must have an elementId and a properties object
def create_node_references(node):
    properties = node.get("properties")
    # Only proceed if there's text to analyze
    if properties and properties.get("text") and len(properties.get("text")) > 0:
        # Get analysis from bedrock
        response = get_agent_response(build_prompt(properties.get("text")))
        # Extract properties of node
        current_document = properties.get("document_title")
        current_section = properties.get("section_number")
        current_subsection = properties.get("subsection_number")
        current_paragraph = properties.get("paragraph_number")
        current_subparagraph = properties.get("subparagraph_number")
        current_related_act = properties.get("related_act_title")
        try:
            references = json.loads(response)
            # For each captured reference
            for reference in references:
                ## Try to find a matching node
                print(reference)
                if reference.get("count") is not None and reference.get("count") > 0:
                    # Only uses this current_related_act with regulations
                    # Otherwise, use the act it identified
                    # Otherwise, use the act of the current node
                    document = (
                        current_related_act
                        if reference.get("this_act") and current_related_act
                        else (reference.get("act") or current_document)
                    )
                    section = reference.get("section") or current_section
                    subsection = reference.get("subsection") or current_subsection
                    paragraph = reference.get("paragraph") or current_paragraph
                    subparagraph = reference.get("subparagraph") or current_subparagraph
                    matching_node = find_node(
                        document, section, subsection, paragraph, subparagraph
                    )
                    if matching_node is not None:
                        print(matching_node)
                        ## Are these the same node? We don't need circular references.
                        if node.get("elementId") != matching_node:
                            ## Is there already an edge to that node?
                            existing_edge = get_ref_edge(
                                node.get("elementId"), matching_node
                            )
                            if existing_edge:
                                ### Yes: increase its weight by this reference's count
                                update_edge_weight(
                                    existing_edge.get("elementId"),
                                    existing_edge.get("weight")
                                    + reference.get("count"),
                                )
                            else:
                                ### No: create the edge with this reference's count as the weight
                                create_edge(
                                    node.get("elementId"),
                                    matching_node,
                                    reference.get("count"),
                                )
        except Exception as e:
            print("failure to parse")
            print(e)


### TESTING AREA
## Replace elementIds with the head nodes of acts or regulations
# Act
testing_nodes = get_whole_tree("4:c3c28288-353b-4525-ba84-6cb5f48d0fb8:231731")
print(testing_nodes[0])
for node in testing_nodes:
    create_node_references(node)

# Regulation
testing_nodes = get_whole_tree("4:c3c28288-353b-4525-ba84-6cb5f48d0fb8:231730")
for node in testing_nodes:
    create_node_references(node)
