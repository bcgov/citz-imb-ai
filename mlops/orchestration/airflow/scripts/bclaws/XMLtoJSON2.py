import os
import json
import xmlschema

def xml_to_json(xml_file, xsd_file, json_file):
    # Create XMLSchema object
    schema = xmlschema.XMLSchema(xsd_file)

    # Validate XML against XSD
    if not schema.is_valid(xml_file):
        print(f"XML file {xml_file} is not valid according to the XSD schema.")
        return

    # Convert XML to dict
    xml_dict = schema.to_dict(xml_file)

    # Write dict to JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(xml_dict, f, ensure_ascii=False, indent=2)

    print(f"Successfully converted {xml_file} to {json_file}")

def process_folder(xml_folder, xsd_file, json_folder):
    # Ensure the output JSON folder exists
    os.makedirs(json_folder, exist_ok=True)

    # Process all XML files in the folder and its subfolders
    for root, _, files in os.walk(xml_folder):
        for file in files:
            if file.endswith('.xml'):
                xml_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, xml_folder)
                json_subfolder = os.path.join(json_folder, relative_path)
                os.makedirs(json_subfolder, exist_ok=True)
                json_file = os.path.join(json_subfolder, f"{os.path.splitext(file)[0]}.json")
                xml_to_json(xml_file, xsd_file, json_file)

if __name__ == "__main__":
    xml_folder = "./xml/Acts"  # Replace with your XML folder path
    xsd_file = "./xsd/act.xsd"  # Replace with your XSD file path
    json_folder = "./json"  # Replace with your desired JSON output folder path

    process_folder(xml_folder, xsd_file, json_folder)
