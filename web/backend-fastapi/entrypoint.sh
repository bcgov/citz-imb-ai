#!/bin/sh

# Load environment variables
echo "Loading environment variables..."

export AWS_ACCESS_KEY_ID="A"



# Check if the environment variables are loaded correctly
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Required environment variable not set. Exiting..."
    exit 1
fi

echo "Environment variables loaded."

# Start the server
echo "Starting the server..."
exec "$@"
