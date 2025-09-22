"""
Video Image Display Tool for Strands Agents

This tool displays images from video search results when the content type is 'image'.
It downloads images from S3 and displays them in Jupyter notebooks.
"""

import os
import boto3
from PIL import Image as PILImage
from IPython.display import display
from typing import Dict, Any, List
from strands import tool


@tool
def display_video_images(
    search_results: List[Dict[str, Any]],
    region: str = None,
    base_path: str = "images/"
) -> Dict[str, Any]:
    """
    Display images from video search results.
    
    Args:
        search_results: List of search results from video_embeddings_aws
        region: AWS region for S3 client
        base_path: Local path to save downloaded images
        
    Returns:
        Dictionary with display results and status
    """
    
    try:
        # Create images directory if it doesn't exist
        os.makedirs(base_path, exist_ok=True)
        
        s3_client = boto3.client('s3', region_name=region)
        
        displayed_count = 0
        text_count = 0
        
        for i, result in enumerate(search_results):
            metadata = result.get('metadata', {})
            content_type = metadata.get('content_type', 'unknown')
            
            if content_type == "text":
                text_count += 1
                print(f"📝 Text Result {text_count}:")
                print(f"   Content: {result.get('content_preview', '')}")
                print(f"   Metadata: {metadata}")
                print()
                
            elif content_type == "image":
                displayed_count += 1
                print(f"🖼️  Image Result {displayed_count}:")
                
                source_url = metadata.get('source', '')
                if source_url.startswith('s3://'):
                    try:
                        # Parse S3 URL
                        parts = source_url.split('s3://')[-1].split('/', 1)
                        bucket_name = parts[0]
                        key = parts[1]
                        filename = source_url.split('/')[-1]
                        
                        print(f"   Source: {source_url}")
                        print(f"   Bucket: {bucket_name}")
                        print(f"   Key: {key}")
                        
                        # Download image from S3
                        local_path = os.path.join(base_path, filename)
                        s3_client.download_file(bucket_name, key, local_path)
                        
                        # Display image
                        img = PILImage.open(local_path)
                        print(f"   Metadata: {metadata}")
                        display(img)
                        print()
                        
                    except Exception as e:
                        print(f"   ❌ Error displaying image: {str(e)}")
                        print()
                else:
                    print(f"   ⚠️  Non-S3 source: {source_url}")
                    print()
        
        return {
            "status": "success",
            "images_displayed": displayed_count,
            "text_results": text_count,
            "total_processed": len(search_results),
            "base_path": base_path
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to display images: {str(e)}"
        }


def download_file_from_s3(bucket_name: str, key: str, local_path: str, s3_client) -> bool:
    """Helper function to download file from S3."""
    try:
        s3_client.download_file(bucket_name, key, local_path)
        return True
    except Exception as e:
        print(f"Error downloading {key}: {str(e)}")
        return False


# Tool metadata
__tool_name__ = "display_video_images"
__tool_description__ = "Display images from video search results"
__tool_version__ = "1.0.0"
__tool_author__ = "Video Embeddings Team"
__tool_tags__ = ["video", "images", "display", "s3", "jupyter"]
