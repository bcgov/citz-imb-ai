import boto3
import os

S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

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
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH, mode=0o777)
    for obj in response['Contents']:
        newpath = os.path.join(BASE_PATH, obj['Key'].split('/')[-1])
        #print(newpath)
        if (newpath != path):
            print(newpath)
            client.download_file(bucket_name, obj['Key'], newpath)

download_data("bclaws/data/html/Cleaned/Acts", "HTML_Acts/", bucket_name)
download_data("bclaws/data/html/Cleaned/Regulations", "HTML_Regulations/", bucket_name)