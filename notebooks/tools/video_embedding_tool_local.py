from strands import tool
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional

# Add the helper directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'create_audio_video_helper'))

from video_manager import VideoManager
from video_processor import VideoProcessor
from embedding_generation import EmbeddingGeneration
from aurora_service import AuroraPostgres
from audio_processing import AudioProcessing
from compare_frames import CompareFrames
from video_s3_uploader import UploadVideoS3

@tool
def video_embedding_local(
    video_path: str,
    user_id: str = "default_user",
    action: str = "process",
    query: Optional[str] = None,
    similarity_threshold: float = 0.8,
    frames_per_second: int = 1,
    region: str = None,
) -> Dict[str, Any]:
    """
    Simple video embedding processor following notebook 05 pattern exactly.
    
    Args:
        video_path: Path to video file (local)
        user_id: User identifier for data isolation
        action: Action to perform ('process', 'search', 'list')
        query: Search query for retrieval (when action is 'search')
        similarity_threshold: Threshold for frame similarity comparison (0.0-1.0)
        frames_per_second: Frames to extract per second
        region: AWS region
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Get configuration from environment
        cluster_arn = os.getenv('AURORA_CLUSTER_ARN')
        secret_arn = os.getenv('AURORA_SECRET_ARN')
        database_name = os.getenv('AURORA_DATABASE_NAME', 'kbdata')
        s3_bucket = os.getenv('AWS_S3_BUCKET', 'langchain-video-embeddings')
        
        if not cluster_arn or not secret_arn:
            return {
                "status": "error",
                "message": "Aurora cluster ARN and secret ARN must be configured in environment variables"
            }
        
        # Initialize Aurora
        aurora = AuroraPostgres(cluster_arn, database_name, secret_arn, region)
        
        if action == "search":
            return _search_videos(query, aurora, region)
        elif action == "list":
            return _list_videos(user_id, aurora)
        else:
            return _process_video(video_path, user_id, similarity_threshold, frames_per_second, 
                                s3_bucket, aurora, region)
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "error_type": type(e).__name__
        }


def _process_video(video_path: str, user_id: str, similarity_threshold: float, 
                  frames_per_second: int, s3_bucket: str, aurora: AuroraPostgres, region: str) -> Dict[str, Any]:
    """Process video following notebook 05 pattern exactly."""
    
    print("🎬 Starting video processing...")
    
    try:
        # 1. Upload video to S3
        print("📤 Uploading video to S3...")
        uploader = UploadVideoS3(s3_bucket)
        video_filename = os.path.basename(video_path)
        s3_key = f"videos/{user_id}/{video_filename}"
        s3_uri = uploader.upload_video_to_s3(video_path, s3_key)
        print(f"✅ Video uploaded: {s3_uri}")
        
        # 2. Initialize VideoManager with S3 URI
        videomanager = VideoManager(s3_uri, region)
        
        # 3. Parse location and download file
        bucket, prefix, fileName, extension, file = videomanager.parse_location(s3_uri)
        
        with tempfile.TemporaryDirectory() as tmp_path:
            local_path = f"{tmp_path}/{file}"
            location = f"{prefix}/{file}"
            output_dir = f"{tmp_path}/{fileName}"
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            print(f"📥 Downloading s3://{bucket}/{prefix}/{file} to {local_path}")
            result = videomanager.download_file(bucket, location, local_path)
            
            if not result:
                return {"status": "error", "message": "Failed to download video from S3"}
            
            # 4. Extract frames using VideoProcessor
            print("🎞️ Extracting frames...")
            videoprocessor = VideoProcessor()
            files = videoprocessor.extract_frames(local_path, output_dir, every=frames_per_second)
            print(f"✅ Extracted {len(files)} frames")
            
            # 5. Generate embeddings for all frames
            print("🧠 Generating frame embeddings...")
            default_model_id = "amazon.titan-embed-image-v1"
            default_embedding_dimension = 1024
            embedding_generation = EmbeddingGeneration(videomanager, region, default_model_id, default_embedding_dimension)
            embed_1024 = embedding_generation.get_images_embeddings(files)
            
            # 6. Filter relevant frames
            print("🔍 Selecting key frames...")
            compareframes = CompareFrames()
            selected_frames = compareframes.filter_relevant_frames(embed_1024, difference_threshold=similarity_threshold)
            print(f"✅ Selected {len(selected_frames)} key frames from {len(embed_1024)} total")
            
            # 7. Create selected frames files tuples
            selected_frames_files = [(sf, files[sf]) for sf in selected_frames]
            
            # 8. Process audio
            print("🎵 Processing audio...")
            text_embeddings = []
            try:
                audio_processing = AudioProcessing(region, videomanager)
                job_name = audio_processing.transcribe(s3_uri)
                if job_name:
                    transcript_url = audio_processing.wait_transcription_complete(job_name)
                    if transcript_url:
                        transcripts, duration = audio_processing.process_transcript(transcript_url, max_chars_per_segment=1000)
                        text_embeddings = embedding_generation.create_text_embeddings(transcripts, s3_uri)
                        print(f"✅ Generated {len(text_embeddings)} text embeddings from {duration}s audio")
                    else:
                        print("⚠️ No transcript URL available")
                else:
                    print("⚠️ Transcription job failed to start")
            except Exception as e:
                print(f"⚠️ Audio processing failed: {e}")
            
            # 9. Create frame embeddings
            print("📊 Creating structured embeddings...")
            frames_embeddings = embedding_generation.create_frames_embeddings(selected_frames_files, s3_uri)
            
            # 10. Store in Aurora
            print("💾 Storing embeddings in Aurora...")
            total_stored = 0
            
            if text_embeddings:
                aurora.insert(text_embeddings)
                total_stored += len(text_embeddings)
                print(f"✅ Stored {len(text_embeddings)} text embeddings")
            
            if frames_embeddings:
                aurora.insert(frames_embeddings)
                total_stored += len(frames_embeddings)
                print(f"✅ Stored {len(frames_embeddings)} frame embeddings")
            
            print(f"🎉 Processing completed! Total embeddings stored: {total_stored}")
            
            return {
                "status": "success",
                "video_s3_uri": s3_uri,
                "total_frames": len(files),
                "key_frames": len(selected_frames),
                "text_embeddings": len(text_embeddings),
                "frame_embeddings": len(frames_embeddings),
                "total_stored": total_stored
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Processing failed: {str(e)}"
        }


def _search_videos(query: str, aurora: AuroraPostgres, region: str) -> Dict[str, Any]:
    """Search video content using embeddings following notebook 05 pattern."""
    try:
        # Create VideoManager and EmbeddingGeneration exactly like notebook 05
        temp_videomanager = VideoManager("s3://temp/temp.mp4", region)
        embedding_generation = EmbeddingGeneration(temp_videomanager, region, "amazon.titan-embed-image-v1", 1024)
        
        # Generate embedding for query exactly like notebook 05
        search_vector = embedding_generation.get_embeddings(query)
        
        # Search in Aurora exactly like notebook 05
        result = aurora.similarity_search(search_vector, how="cosine", k=10)
        
        # Parse results exactly like notebook 05
        import json
        rows = json.loads(result.get("formattedRecords"))
        
        return {
            "status": "success",
            "query": query,
            "results": rows,
            "total_found": len(rows)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }


def _list_videos(user_id: str, aurora: AuroraPostgres) -> Dict[str, Any]:
    """List all videos since user_id is not stored in metadata in notebook 05."""
    try:
        # Simple query to get all videos (no user filtering since it's not in notebook 05)
        sql = """
        SELECT DISTINCT sourceurl, content_type, COUNT(*) as embedding_count, 
               MIN(date) as first_processed
        FROM bedrock_integration.knowledge_bases 
        GROUP BY sourceurl, content_type
        ORDER BY first_processed DESC
        """
        
        result = aurora.execute_statement(sql)
        
        videos = []
        # Handle Aurora response format like notebook 05
        if 'formattedRecords' in result:
            import json
            records = json.loads(result['formattedRecords'])
            for record in records:
                videos.append({
                    "sourceurl": record.get('sourceurl'),
                    "content_type": record.get('content_type'), 
                    "embedding_count": record.get('embedding_count'),
                    "first_processed": record.get('first_processed')
                })
        
        return {
            "status": "success",
            "user_id": user_id,
            "videos": videos,
            "total_videos": len(videos)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"List failed: {str(e)}"
        }
