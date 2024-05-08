import boto3
import os

def downloadlawtitles():
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

    linode_obj_config = {
        "aws_access_key_id": S3_ACCESS_KEY,
        "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
        "endpoint_url": S3_ENDPOINT_URL,
    }
    bucket_name = "IMBAIPilot"

    prefix = "bclaws/data/txt/all_act_titles.txt"

    client = boto3.client("s3", **linode_obj_config)

    paginator = client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    BASE_PATH = "DB/RawBCLaws/"
    count = 0

    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH, mode=0o777)

    for page in pages:
        for obj in page['Contents']:
            newpath = os.path.join(BASE_PATH, obj['Key'].split('/')[-1])
            count +=1
            print(f"docuument # {count}")
            if newpath != "RawBCLaws/":
                print(newpath)
                client.download_file(bucket_name, obj['Key'], newpath)