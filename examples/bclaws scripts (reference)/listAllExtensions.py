import os

def list_file_extensions(directory):
    # Set to store unique file extensions
    extensions = set()
    
    # Walk through all directories and files in the given directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get the extension of the current file
            _, ext = os.path.splitext(file)
            if ext:  # Check if there is an extension
                extensions.add(ext)
    
    # Print all unique extensions sorted
    for ext in sorted(extensions):
        print(ext)

# Specify the directory path here
directory_path = './images'
list_file_extensions(directory_path)
