"""
Comments for 01_query_audio_video_embeddings.ipynb

This script contains comments that should be added to the notebook to explain its purpose and functionality.
"""

# Add at the beginning of the notebook
INTRO_COMMENT = """
# Query Audio/Video Embeddings Notebook
This notebook demonstrates how to query and analyze video and audio content that has been processed and stored in the Aurora PostgreSQL vector database. You can use this notebook to:

1. Connect to your Aurora PostgreSQL vector database
2. Generate embeddings for search queries using Amazon Bedrock
3. Perform semantic searches on your processed audio/video content
4. Visualize image frames extracted from videos
5. Build and test RAG (Retrieval Augmented Generation) applications

Before running this notebook, ensure you have:
- Deployed the complete audio/video embeddings processing application stack
- Processed at least one video through the workflow
- Set up the necessary AWS credentials and permissions
"""

# Add before the imports section
SETUP_COMMENT = """
# Setup and Configuration
The following cells import necessary libraries and set up connections to AWS services.
Make sure you have the required packages installed and AWS credentials configured.
"""

# Add before the database connection section
DATABASE_COMMENT = """
# Database Connection
These cells establish a connection to the Aurora PostgreSQL database using the RDS Data API.
The connection parameters are retrieved from AWS Systems Manager Parameter Store.
"""

# Add before the retrieval function
RETRIEVAL_COMMENT = """
# Semantic Search Implementation
The `retrieve()` function below performs semantic searches on your processed content:
1. Generates embeddings for your search query using Amazon Bedrock
2. Performs a vector similarity search in the Aurora PostgreSQL database
3. Displays the results, including text content and image frames
4. Returns the matching documents for further processing

You can adjust the similarity method ('cosine' or 'l2') and the number of results (k).
"""

# Add before the RAG implementation
RAG_COMMENT = """
# RAG (Retrieval Augmented Generation) Implementation
The following cells implement a complete RAG system using:
1. A custom retriever class that extends LangChain's BaseRetriever
2. Functions to format content for LLM consumption
3. Integration with Amazon Bedrock for generating AI responses

This allows you to ask questions about your video content and receive AI-generated answers
based on the retrieved information.
"""

# Add before the Lambda function section
LAMBDA_COMMENT = """
# Query Through Lambda Function
These cells demonstrate how to invoke the retrieval Lambda function directly.
This is useful for testing the Lambda function's behavior or for integrating
with other applications.
"""
