import os
import xmlschema
import xmltodict
import json

# Define the path to the folder containing the XML files
xml_folder_path = 'xml/Final/Acts'

# Define the path to the XSD file
xsd_file_path = 'xsd/act.xsd'

# Define the path to the output folder for JSON files
json_folder_path = 'json'

# Create the output folder if it doesn't exist
os.makedirs(json_folder_path, exist_ok=True)

# Load the XSD schema
schema = xmlschema.XMLSchema(xsd_file_path)

# Iterate through each XML file in the folder
for filename in os.listdir(xml_folder_path):
    if filename.endswith('.xml'):
        xml_file_path = os.path.join(xml_folder_path, filename)

        # Validate the XML file against the XSD schema
        is_valid = schema.is_valid(xml_file_path)
        if not is_valid:
            print(f"Skipping '{filename}' as it does not conform to the XSD schema.")
            continue

        # If the XML is valid, proceed with the conversion
        with open(xml_file_path, 'r') as xml_file:
            xml_data = xml_file.read()
            dict_data = xmltodict.parse(xml_data)
            json_data = json.dumps(dict_data, indent=4)

            # Construct the output JSON file path
            json_file_path = os.path.join(json_folder_path, os.path.splitext(filename)[0] + '.json')

            # Save the JSON data to the file
            with open(json_file_path, 'w') as json_file:
                json_file.write(json_data)

            print(f"XML '{filename}' has been successfully converted to JSON and saved to '{json_file_path}'.")
