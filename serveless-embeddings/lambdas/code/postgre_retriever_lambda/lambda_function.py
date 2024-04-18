"""
EVENT
{
    "location": "YOU-KEY",
    "collectioName": "YOU-COLLECTION-NAME",
    "bucketName": "YOU-BUCKET",
    "fileType": "image or pdf",
    "embeddingModel": "amazon.titan-embed-image-v1", 
    "llmModel": "anthropic.claude-3-sonnet-20240229-v1:0",
    "QUERY": "YOU QUESTION",
    "PGVECTOR_USER":"PGVECTOR_USER",
    "PGVECTOR_PASSWORD":"PGVECTOR_PASSWORD",
    "PGVECTOR_HOST":"PGVECTOR_HOST",
    "PGVECTOR_DATABASE":"PGVECTOR_DATABASE"
  }
"""
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_community.chat_models import BedrockChat
from langchain.chains import RetrievalQA
from langchain.callbacks import StdOutCallbackHandler
from langchain_community.embeddings import BedrockEmbeddings # to create embeddings for the documents.
from sqlalchemy import create_engine
import json
import base64
import boto3
from utils import (build_response, download_file)

bedrock_client              = boto3.client("bedrock-runtime") 

### Retrieve information using Amazon Bedrock
def retrieve_information(llm, vectordb,query):
    # Set up the retrieval chain with the language model and database retriever
    chain = RetrievalQA.from_chain_type(
                                            llm=llm,
                                            retriever=vectordb.as_retriever(),
                                            verbose=True
                                        )

    # Initialize the output callback handler
    handler = StdOutCallbackHandler()

    # Run the retrieval chain with a query
    chain_value = chain.run(
                query,
                callbacks=[handler]
            )
    return chain_value

# function to create vector store
def create_vectorstore(embeddings,collection_name,conn):
                       
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=conn,
        use_jsonb=True,
    )
    return vectorstore

# Función para convertir una imagen a base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    vector = get_multimodal_vector(input_image_base64=encoded_string)
    return encoded_string, vector

#calls Bedrock to get a vector from either an image, text, or both
def get_multimodal_vector(input_image_base64=None, input_text=None):
    request_body = {}
    if input_text:
        request_body["inputText"] = input_text
        
    if input_image_base64:
        request_body["inputImage"] = input_image_base64
    
    body = json.dumps(request_body)
    response = bedrock_client.invoke_model(
    	body=body, 
    	modelId="amazon.titan-embed-image-v1", 
    	accept="application/json", 
    	contentType="application/json"
    )

    response_body = json.loads(response.get('body').read())
    
    embedding = response_body.get("embedding")
    
    return embedding

def lambda_handler(event, context):
    print("event:", event)

    location                = event.get("location")
    collection_name         = event.get("collectioName")
    bucket_name             = event.get("bucketName")
    file_type               = event.get("fileType")
    embedding_model         = event.get("embeddingModel")
    user                    = event.get("PGVECTOR_USER")
    password                = event.get("PGVECTOR_PASSWORD")
    host                    = event.get("PGVECTOR_HOST")
    database                = event.get("PGVECTOR_DATABASE")
    llmModel                = event.get("llmModel")
    query                   = event.get("QUERY")

    llm = BedrockChat(model_id=llmModel, client=bedrock_client)
    bedrock_embeddings          = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)
    # Create the SQLAlchemy engine
    engine = create_engine(f"postgresql://{user}:{password}@{host}/{database}") 
    tmp_path                    = "/tmp"

    if file_type == "pdf":
        vectorstore = create_vectorstore(bedrock_embeddings,collection_name,engine)
        response = retrieve_information(llm, vectorstore,query) 
        print(f"Response: {response} ")

    elif file_type == "image":
        image_vectorstore = create_vectorstore(bedrock_embeddings,collection_name,engine)
        if event.get("location"):
            file_name              = location.split("/")[-1]
            local_file             = f"{tmp_path}/{file_name}"
            print(f"dowload from s3://{bucket_name}{location} to {local_file}")
            download_file(bucket_name,location, local_file)
            image_base64, image_embedding = image_to_base64(local_file)
            response = image_vectorstore.similarity_search_with_score_by_vector(image_embedding)

        else:
            response = retrieve_information(llm, image_vectorstore,query)
       
    event["response"] = response
    print(f"Response: {response} ")

    return build_response(200, json.dumps(event))