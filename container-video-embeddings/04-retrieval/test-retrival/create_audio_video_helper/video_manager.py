import boto3
import os
import json
from urllib.parse import unquote

"""
- `parse_location()`: Parses S3 URIs into bucket, prefix, filename components
- `read_json_from_s3()`: Reads JSON files from S3 buckets
- `download_file()`: Downloads files from S3 to local storage
- `upload_file()`: Uploads local files to S3
- `read_image_from_s3()`: Reads image files directly from S3
- `read_image_from_local()`: Reads image files from local storage
"""

class VideoManager:

    def __init__(self, s3_uri,region_name):
        self.s3_uri = s3_uri
        self.s3 = boto3.client(service_name="s3", region_name= region_name)

    def parse_location(self,s3_uri):
        [_, part] = s3_uri.split("s3://")
        elements = part.split("/")
        bucket = elements[0]
        prefix = "/".join(elements[1:-1])
        file = elements[-1]
        [fileName, extension] = file.split(".")
        return bucket, prefix, fileName, extension, file

    def read_json_from_s3(self,s3_uri):

        # Handle URL encoded characters in s3_uri
        
        s3_uri = unquote(s3_uri)

        parts = s3_uri.split('s3://')[-1].split('/', 1)
        bucket_name = parts[0]
        json_key = parts[1]
        
        try:
            response = self.s3.get_object(Bucket=bucket_name, Key=json_key)
            json_data = json.loads(response['Body'].read().decode('utf-8'))
            return json_data
        except Exception as e:
            print(f'Error reading JSON from {s3_uri}: {str(e)}')
            raise


    def download_file(self,bucket, key, filename):
        # first check if filename exists
        if os.path.exists(filename):
            print("File already exists")
            return True
        try:
            self.s3.download_file(bucket, key, filename)
            print("File downloaded successfully")
            return True
        except Exception as e:
            print("Error downloading file:", e)
            return False
        
    def upload_file(self,bucket, key, filename):
        try:
            self.s3.upload_file(filename, bucket, key)
            print("File uploaded successfully")
            return True
        except Exception as e:
            print("Error uploading file:", e)
            return False
        
    def read_image_from_s3(self,s3_key):
        parts = s3_key.split('s3://')[-1].split('/', 1)
        bucket_name = parts[0]
        image_key = parts[1]
        response = self.s3.get_object(Bucket=bucket_name, Key=image_key)
        image_data = response['Body'].read()
        return image_data

    def read_image_from_local(self,file_path):
        try:
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
            return image_data
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return None
        except IOError as e:
            print(f"Error reading file: {e}")
            return None
    