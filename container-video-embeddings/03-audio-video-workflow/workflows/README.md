# Video Summarization ECS Workflow

This project implements a Step Functions workflow that processes videos using ECS tasks.

## Workflow Overview

The workflow:
1. Accepts an input with an `s3_uri` attribute pointing to a video file
2. Launches an ECS Fargate task to process the video
3. The ECS task runs `python3 lambda_function.py s3_uri` with the provided S3 URI

## Usage

To use this workflow, provide an input in the following format:

```json
{
  "s3_uri": "s3://your-bucket/path/to/video.mp4"
}
```

## Implementation Details

The workflow uses AWS Step Functions to orchestrate the video processing:

- **ECS Task**: Runs on Fargate with the specified task definition
- **Command Override**: The container command is overridden to run the Python script with the S3 URI
- **Error Handling**: Includes retry logic for various failure scenarios
- **Timeout**: Task timeout is set to 2 hours, with an overall workflow timeout of 4 hours

## Deployment

The workflow is deployed using AWS CDK. The `AudioVideoWorkflow` construct requires:

- An ECS cluster
- A task definition with the appropriate container configuration

Example:
```python
workflow = AudioVideoWorkflow(
    self, "VideoWorkflow",
    cluster=my_cluster,
    task_definition=my_task_definition
)
```
