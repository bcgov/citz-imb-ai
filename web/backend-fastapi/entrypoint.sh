#!/bin/sh

# Load environment variables
echo "Loading environment variables..."

export AWS_ACCESS_KEY_ID="###"
export AWS_SECRET_ACCESS_KEY="###"
export AWS_SESSION_TOKEN="###"
export S3_ACCESS_KEY="###"
export S3_SECRET_ACCESS_KEY="###"
export S3_ENDPOINT_URL="###"

# Check if the environment variables are loaded correctly
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Required environment variable not set. Exiting..."
    exit 1
fi

echo "Environment variables loaded."

echo "Downloading the onnx model..."
python app/models/onnx_s3.py

# Start the server
echo "Starting the server..."
exec "$@"
