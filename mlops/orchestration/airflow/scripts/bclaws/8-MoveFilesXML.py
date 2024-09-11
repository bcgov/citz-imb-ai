import os
import shutil
import xml.etree.ElementTree as ET

def move_files_to_folders(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_path.endswith('.xml'):
            # Check for "Table_of_Contents_" and delete the file if found
            if "Table_of_Contents_" in file_name:
                os.remove(file_path)
                print(f'Deleted {file_name}')
                continue

            # Check for "REPEALED BY B.C." in the file content
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                if any(elem.text and "REPEALED BY B.C." in elem.text for elem in root.iter()):
                    target_folder = os.path.join(folder_path, "Repealed")
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file_name))
                    continue
            except ET.ParseError:
                print(f"Error parsing {file_name}. Skipping...")
                continue

            # Move file to the appropriate folder based on patterns
            if "Edition_TLC" in file_name:
                target_folder = os.path.join(folder_path, "Editions")
            elif file_name.startswith("Historical_Table_"):
                target_folder = os.path.join(folder_path, "Historical Tables")
            elif file_name.startswith("Appendices_") or file_name.startswith("Appendix_"):
                target_folder = os.path.join(folder_path, "Appendix")
            elif file_name.startswith("Chapter_"):
                target_folder = os.path.join(folder_path, "Chapters")
            elif file_name.startswith("Part"):
                target_folder = os.path.join(folder_path, "Parts")
            elif file_name.startswith("Point_in_Time_"):
                target_folder = os.path.join(folder_path, "Point in Times")
            elif "Regulation" in file_name:
                target_folder = os.path.join(folder_path, "Regulations")
            elif "Schedule" in file_name:
                target_folder = os.path.join(folder_path, "Schedules")
            elif "Sections_" in file_name:
                target_folder = os.path.join(folder_path, "Sections")
            elif "Rule" in file_name:
                target_folder = os.path.join(folder_path, "Rules")
            elif file_name.endswith("_Act.xml"):
                target_folder = os.path.join(folder_path, "Acts")
            else:
                # Move remaining files to the "Others" folder
                target_folder = os.path.join(folder_path, "Others")

            # Create the target folder if it doesn't exist and move the file
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))

if __name__ == '__main__':
    xml_folder = 'xml'  # Change this to your XML folder name
    move_files_to_folders(xml_folder)
