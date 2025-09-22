"""
Video Embeddings AWS Tool for Strands Agents

This tool provides video processing and retrieval capabilities using deployed AWS infrastructure
from the container-video-embeddings CDK stacks. It leverages Lambda functions, API Gateway,
and Step Functions for scalable video processing and semantic search.

Features:
- Upload videos to S3 and trigger automated processing
- Search video content using semantic similarity
- List processed videos and their metadata
- Uses deployed AWS infrastructure (no local processing required)

Requirements:
- AWS credentials configured
- Deployed container-video-embeddings infrastructure
- SSM parameters configured with infrastructure endpoints
"""

import os
import json
import time
import boto3
import requests
from typing import Dict, Any, Optional, List
from strands import tool


@tool
def video_embeddings_aws(
    action: str,
    video_path: Optional[str] = None,
    query: Optional[str] = None,
    region: str = None,
    max_wait_time: int = 300,
    k: int = 10
) -> Dict[str, Any]:
    """
    Process and search video content using deployed AWS infrastructure.
    
    This tool uses the container-video-embeddings CDK stacks to process videos
    and perform semantic search on video content. All processing happens in AWS
    using Lambda functions, ECS tasks, and Aurora PostgreSQL with pgvector.
    
    Args:
        action: Action to perform ('process', 'search', 'list')
        video_path: Path to local video file (required for 'process' action)
        query: Search query text (required for 'search' action)  
        region: AWS region where infrastructure is deployed
        max_wait_time: Maximum time to wait for processing completion (seconds)
        k: Number of results to return for search (default: 10)
        
    Returns:
        Dictionary with operation results and status information
        
    Examples:
        # Process a video file
        result = video_embeddings_aws(
            action="process",
            video_path="/path/to/video.mp4"
        )
        
        # Search video content
        result = video_embeddings_aws(
            action="search", 
            query="people talking about technology",
            k=5
        )
        
        # List processed videos
        result = video_embeddings_aws(
            action="list"
        )
    """
    
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3', region_name=region)
        ssm_client = boto3.client('ssm', region_name=region)
        
        # Get infrastructure endpoints from SSM Parameter Store
        try:
            api_endpoint = _get_ssm_parameter(ssm_client, "/videopgvector/api_retrieve")
            s3_bucket = _get_ssm_parameter(ssm_client, "/videopgvector/bucket_name")
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get infrastructure configuration: {str(e)}",
                "help": "Ensure the container-video-embeddings CDK stacks are deployed and SSM parameters exist"
            }
        
        # Route to appropriate handler based on action
        if action == "process":
            if not video_path:
                return {
                    "status": "error", 
                    "message": "video_path is required for process action"
                }
            return _process_video_aws(video_path, s3_bucket, s3_client, api_endpoint, max_wait_time)
            
        elif action == "search":
            if not query:
                return {
                    "status": "error",
                    "message": "query is required for search action"
                }
            return _search_videos_aws(query, api_endpoint, k)
            
        elif action == "list":
            return _list_videos_aws(api_endpoint)
            
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Supported actions: process, search, list"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        }


def _get_ssm_parameter(ssm_client, parameter_name: str) -> str:
    """Get parameter value from SSM Parameter Store."""
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    return response["Parameter"]["Value"]


def _process_video_aws(
    video_path: str, 
    s3_bucket: str, 
    s3_client, 
    api_endpoint: str,
    max_wait_time: int
) -> Dict[str, Any]:
    """
    Process video by uploading to S3 and triggering the deployed AWS workflow.
    
    The video processing workflow includes:
    1. Upload video to S3 (triggers Lambda via S3 event)
    2. ECS task extracts frames and audio
    3. Generate embeddings using Bedrock
    4. Store embeddings in Aurora PostgreSQL with pgvector
    5. Step Functions orchestrates the entire workflow
    """
    
    if not os.path.exists(video_path):
        return {
            "status": "error",
            "message": f"Video file not found: {video_path}"
        }
    
    try:
        # Generate S3 key
        video_filename = os.path.basename(video_path)
        s3_key = f"videos/{video_filename}"
        
        # Upload video to S3 with metadata
        print(f"📤 Uploading {video_filename} to S3...")
        metadata = {
            'upload_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'original_filename': video_filename,
            'processing_status': 'uploaded'
        }
        
        s3_client.upload_file(
            video_path,
            s3_bucket, 
            s3_key,
            ExtraArgs={'Metadata': metadata}
        )
        
        s3_uri = f"s3://{s3_bucket}/{s3_key}"
        print(f"✅ Video uploaded: {s3_uri}")
        print("🔄 AWS processing workflow triggered automatically...")
        
        # Monitor processing status by checking for embeddings
        print(f"⏳ Monitoring processing status (max wait: {max_wait_time}s)...")
        start_time = time.time()
        check_interval = 10  # Check every 10 seconds
        
        while (time.time() - start_time) < max_wait_time:
            # Check if processing is complete by searching for content from this video
            search_result = _search_videos_aws(video_filename, api_endpoint, 5)
            
            if search_result.get('status') == 'success' and search_result.get('total_found', 0) > 0:
                elapsed_time = int(time.time() - start_time)
                print(f"✅ Processing completed in {elapsed_time}s!")
                
                return {
                    "status": "success",
                    "message": "Video processed successfully",
                    "video_s3_uri": s3_uri,
                    "processing_time_seconds": elapsed_time,
                    "embeddings_created": search_result.get('total_found', 0),
                    "workflow": "AWS Step Functions + ECS + Lambda",
                    "storage": "Aurora PostgreSQL with pgvector"
                }
            
            elapsed_time = int(time.time() - start_time)
            print(f"⏳ Still processing... ({elapsed_time}s elapsed)")
            time.sleep(check_interval)
        
        # Processing timeout
        elapsed_time = int(time.time() - start_time)
        return {
            "status": "processing",
            "message": f"Video uploaded and processing started. Timeout after {elapsed_time}s.",
            "video_s3_uri": s3_uri,
            "help": "Processing may still be in progress. Check back later or increase max_wait_time."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Video processing failed: {str(e)}"
        }


def _search_videos_aws(query: str, api_endpoint: str, k: int = 10) -> Dict[str, Any]:
    """
    Search video content using the deployed API Gateway and Lambda function.
    
    The search process:
    1. Query sent to API Gateway endpoint
    2. Lambda function generates query embedding using Bedrock
    3. Performs vector similarity search in Aurora PostgreSQL
    4. Returns ranked results with similarity scores
    """
    
    try:
        print(f"🔍 Searching for: '{query}'")
        
        # Call the deployed retrieval API with correct payload structure
        payload = {
            "query": query,
            "method": "retrieve",
            "k": k
        }
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse the response based on the Lambda function structure
            if 'docs' in result:
                docs_data = result['docs']
                if isinstance(docs_data, str):
                    docs_data = json.loads(docs_data)
                
                docs = docs_data.get('docs', []) if isinstance(docs_data, dict) else docs_data
                
                print(f"✅ Found {len(docs)} matching results")
                
                # Format results for better readability
                formatted_results = []
                for item in docs:
                    metadata = item.get('metadata', {})
                    formatted_results.append({
                        "content_type": metadata.get('content_type', 'unknown'),
                        "similarity_score": round(float(item.get('similarity', 0)), 3),
                        "source": metadata.get('source', 'N/A'),
                        "content_preview": item.get('page_content', '')[:200] + "..." if item.get('page_content') else "",
                        "metadata": metadata,
                        "timestamp": metadata.get('time', 'N/A')
                    })
                
                return {
                    "status": "success",
                    "query": query,
                    "results": formatted_results,
                    "total_found": len(docs),
                    "search_method": "Vector similarity (cosine distance)",
                    "embedding_model": "Amazon Titan Embed"
                }
            else:
                return {
                    "status": "error",
                    "message": "Unexpected response format from API",
                    "details": str(result)
                }
        else:
            return {
                "status": "error", 
                "message": f"API request failed: HTTP {response.status_code}",
                "details": response.text
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Search request timed out. The API may be overloaded."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }


def _list_videos_aws(api_endpoint: str) -> Dict[str, Any]:
    """
    List processed videos for a user by querying the API.
    
    This performs a user-specific search to find all videos processed for the given user_id.
    """
    
    try:
        print(f"📋 Listing all processed videos")
        
        # Use a broad search to find all content
        payload = {
            "query": "*",  # Search for all content
            "method": "retrieve",
            "k": 100  # Get more results for comprehensive listing
        }
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse the response based on the Lambda function structure
            if 'docs' in result:
                docs_data = result['docs']
                if isinstance(docs_data, str):
                    docs_data = json.loads(docs_data)
                
                docs = docs_data.get('docs', []) if isinstance(docs_data, dict) else docs_data
                
                # Group results by source video to get unique videos
                videos_map = {}
                for item in docs:
                    metadata = item.get('metadata', {})
                    source = metadata.get('source', 'unknown')
                    if source not in videos_map:
                        videos_map[source] = {
                            'source_url': source,
                            'content_type': metadata.get('content_type', 'unknown'),
                            'embedding_count': 1,
                            'first_processed': metadata.get('date', 'unknown'),
                            'metadata': metadata
                        }
                    else:
                        videos_map[source]['embedding_count'] += 1
                
                video_list = list(videos_map.values())
                print(f"✅ Found {len(video_list)} processed videos")
                
                return {
                    "status": "success",
                    "videos": video_list,
                    "total_videos": len(video_list),
                    "total_embeddings": len(docs),
                    "storage": "Aurora PostgreSQL with pgvector"
                }
            else:
                return {
                    "status": "error",
                    "message": "Unexpected response format from API",
                    "details": str(result)
                }
        else:
            return {
                "status": "error",
                "message": f"API request failed: HTTP {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"List operation failed: {str(e)}"
        }


# Tool metadata for Strands registry
__tool_name__ = "video_embeddings_aws"
__tool_description__ = "Process and search video content using deployed AWS infrastructure"
__tool_version__ = "1.0.0"
__tool_author__ = "Container Video Embeddings Team"
__tool_tags__ = ["video", "embeddings", "aws", "search", "ai", "bedrock", "aurora"]
