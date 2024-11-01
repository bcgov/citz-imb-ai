#!/bin/sh

# Load environment variables
echo "Loading environment variables..."

export AWS_SESSION_TOKEN="--"
export AWS_DEFAULT_REGION=ca-central-1
export AWS_REGION=ca-central-1

# Check if the environment variables are loaded correctly
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Required environment variable not set. Exiting..."
    exit 1
fi

echo "Environment variables loaded."

# Start the server
echo "Starting the server..."
exec "$@"
