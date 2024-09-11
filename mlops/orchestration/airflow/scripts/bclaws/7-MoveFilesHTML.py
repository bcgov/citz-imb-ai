import os
import shutil

def move_files_to_folders(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and file_path.endswith('.html'):
            # Check for "Table_of_Contents_" and delete the file if found
            if "Table_of_Contents_" in file_name:
                os.remove(file_path)
                print(f'Deleted {file_name}')
                continue

            # Check for "<strong>REPEALED BY B.C." in the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                if "<strong>REPEALED BY B.C." in file.read():
                    target_folder = os.path.join(folder_path, "Repealed")
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file_name))
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
            elif file_name.endswith("_Act.html"):
                target_folder = os.path.join(folder_path, "Acts")
            else:
                # Move remaining files to the "Others" folder
                target_folder = os.path.join(folder_path, "Others")

            # Create the target folder if it doesn't exist and move the file
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))

if __name__ == '__main__':
    downloads_folder = 'html'
    move_files_to_folders(downloads_folder)
