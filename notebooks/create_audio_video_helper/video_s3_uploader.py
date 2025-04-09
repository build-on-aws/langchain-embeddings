"""
Simple S3 Video Uploader

A lightweight module to upload video files from a temporary folder to an S3 bucket.
"""

import os
import boto3
import logging
from typing import List, Dict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from pathlib import Path

class UploadVideoS3:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')

    def upload_video_to_s3(self, video_path, s3_key=None):
        """
        Upload a video file to an S3 bucket and return the S3 URI.

        Parameters:
        -----------
        video_path : str
            Local path to the video file
        s3_key : str, optional
            The S3 key (path) where the video will be stored. If not provided,
            the filename from video_path will be used.

        Returns:
        --------
        str
            The S3 URI of the uploaded video (s3://bucket-name/key)
        """
        # Check if the file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # If s3_key is not provided, use the filename from video_path
        if s3_key is None:
            s3_key = Path(video_path).name

        try:
            # Upload the file
            print(f"Uploading {video_path} to s3://{self.bucket_name}/{s3_key}...")
            self.s3_client.upload_file(video_path, self.bucket_name, s3_key)
            print("Upload successful!")

            # Construct and return the S3 URI
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            return s3_uri

        except Exception as e:
            print(f"Error uploading file to S3: {e}")
            raise

