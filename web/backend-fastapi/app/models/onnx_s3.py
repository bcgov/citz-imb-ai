import boto3
import os

# Load S3 credentials from environment variables
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

# S3 configuration
linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}
bucket_name = "IMBAIPilot"

def download_data(bucket, path, bucket_name):
    prefix = bucket
    client = boto3.client("s3", **linode_obj_config)
    response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    BASE_PATH = path

    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH, mode=0o777)

    for obj in response.get('Contents', []):
        # Construct the local file path
        file_path = os.path.join(BASE_PATH, obj['Key'])
        file_dir = os.path.dirname(file_path)

        # Create directories if they do not exist
        if not os.path.exists(file_dir):
            os.makedirs(file_dir, mode=0o777)

        # Skip if the path is a directory
        if os.path.isdir(file_path):
            print(f"Skipping download because {file_path} is a directory.")
            continue

        # Print the path for debugging
        print(file_path)

        try:
            # Download the file from S3
            client.download_file(bucket_name, obj['Key'], file_path)
            print(f"File downloaded successfully to {file_path}")
        except Exception as e:
            print(f"Error downloading file {obj['Key']}: {e}")

# Download ONNX model from S3
download_data("onnx", "./", bucket_name)