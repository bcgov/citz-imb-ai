#!/bin/bash

# Create the REPEALED directory if it doesn't exist
mkdir -p REPEALED

# Loop through all files in the current directory and subdirectories
find . -type f | while read -r file; do
    # Check if the file contains both '<reg:defunct effective=' and 'REPEALED'
    if grep -q '<reg:defunct effective=' "$file" && grep -q 'REPEALED' "$file"; then
        # Move the file to the REPEALED directory
        mv "$file" REPEALED/
    fi
done
