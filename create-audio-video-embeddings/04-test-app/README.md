# Test Audio Video Embeddings APP

This tool identifies and extracts key frames from video content using deep learning-based image embeddings. It processes video files to find significant visual changes and uploads the selected frames to S3.

## Overview

The system performs the following steps:
1. Downloads a video file from S3
2. Extracts frames at 1 FPS using FFmpeg
3. Generates image embeddings using AWS Bedrock
4. Calculates cosine similarity between consecutive frames
5. Selects frames with significant visual differences
6. Uploads selected key frames back to S3

## Prerequisites
- Deploy [01-ecs-cluster stack](../01-ecs-cluster/README.md)
- Deploy [02-aurora-pg-vector stack](../02-aurora-pg-vector/README.md)
- Deploy [03-audio-video-workflow stack](../03-audio-video-workflow/README.md)
- Python 3.7 or higher
- FFmpeg installed
- AWS credentials configured with access to:
  - Amazon S3
  - Amazon Bedrock

## Required Python Packages

```
boto3
numpy
torch
pillow
```

## Usage

Set the required environment variables:

```python
os.environ['S3_URI'] = 's3://your-bucket/video_in/video_file.mp4'
os.environ['TASK_TOKEN'] = 'optional-step-function-token'  # For AWS Step Functions integration created in 03-audio-video-workflow stack
```

The tool will:
1. Parse the S3 URI to extract bucket and key information
2. Download the video to a temporary directory
3. Process frames and generate embeddings
4. Upload selected frames to S3

### Configuration Parameters

- `tmp_path`: Local directory for temporary files (default: "./tmp")
- `difference_threshold`: Similarity threshold for frame selection (default: 0.9)

### Example Output

Selected frames are saved to S3 with numeric names corresponding to their position in the video:

```
s3://your-bucket/video_in/selected_frames/3.jpg
s3://your-bucket/video_in/selected_frames/237.jpg
s3://your-bucket/video_in/selected_frames/289.jpg
...
```

## Main Components

- `audio_video_embeddings_test.ipynb`: Jupyter notebook to test the app
- `video_processor.py`: Video frame extraction using FFmpeg
- `get_image_embeddings.py`: Generation of image embeddings using Amazon Bedrock
- `similarity.py`: Frame similarity calculation and selection
- `utils.py`: Amazon S3 operations and helper functions
- `step_function_utils.py`: Amazon Step Functions integration

### Processing Pipeline

1. Amazon S3 URI Parsing:
   ```python
   bucket, prefix, fileName, extension, file = parse_location(s3_uri)
   ```

2. Video Download:
   ```python
   download_file(bucket, location, local_path)
   ```

3. Frame Extraction:
   ```python
   files = extract_frames(local_path, output_dir)
   ```

4. Embedding Generation:
   ```python
   embed_1024 = get_images_embeddings(files, embedding_dimmesion=1024)
   ```

5. Similarity Analysis:
   ```python
   similarity_1024 = cosine_similarity_list(embed_1024)
   selected_frames = filter_relevant_frames(similarity_1024, difference_threshold)
   ```

6. Frame Upload:
   ```python
   for frame in selected_frames:
       upload_file(bucket, f"{prefix}/selected_frames/{frame}.jpg", frame_path)
   ```

## Technical Details

- Frames are extracted at 1 FPS and scaled to 1024x576 resolution
- Image embeddings are 1024-dimensional vectors
- Frame selection uses cosine similarity with a default threshold of 0.9
- Selected frames are automatically uploaded to S3 with sequential numbering
- Temporary files are stored in "./tmp" directory
