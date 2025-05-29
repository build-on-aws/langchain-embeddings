"""
Comments for 02_test_webhook.ipynb

This script contains comments that should be added to the notebook to explain its purpose and functionality.
"""

# Add at the beginning of the notebook
INTRO_COMMENT = """
# Test Retrieval API Notebook
This notebook allows you to test the retrieval API endpoints and workflow integration for the audio/video embeddings system. Use this notebook to:

1. Upload video files to the S3 bucket for processing
2. Monitor Step Functions workflow executions
3. Test the retrieval API endpoints with different query parameters
4. Analyze API responses using pandas DataFrames

Before running this notebook, ensure you have:
- Deployed the retrieval API stack
- Access to the S3 bucket for video uploads
- AWS credentials with appropriate permissions
"""

# Add before the AWS client setup
SETUP_COMMENT = """
# Setup and Configuration
The following cells import necessary libraries and set up connections to AWS services.
The API URL and other configuration parameters are retrieved from AWS Systems Manager Parameter Store.
"""

# Add before the upload function
UPLOAD_COMMENT = """
# Video Upload Function
This function uploads a video file to the configured S3 bucket, which triggers the processing workflow.
The workflow extracts frames, generates transcripts, and creates embeddings for the video content.
"""

# Add before the Step Functions monitoring
WORKFLOW_COMMENT = """
# Step Functions Workflow Monitoring
These cells allow you to check the status of the Step Functions workflow that processes your video.
You can monitor the execution status and wait for the processing to complete before testing the API.
"""

# Add before the API testing section
API_COMMENT = """
# Retrieval API Testing
The following cells demonstrate how to send requests to the retrieval API endpoints:
1. Basic retrieval query: Returns relevant content based on your search query
2. Retrieval with AI generation: Returns both retrieved content and an AI-generated response

You can adjust the query parameters to test different search scenarios.
"""

# Add before the DataFrame visualization
VISUALIZATION_COMMENT = """
# Results Visualization
These cells convert the API response into a pandas DataFrame for easier analysis.
You can see the retrieved documents, their similarity scores, and other metadata.
"""
