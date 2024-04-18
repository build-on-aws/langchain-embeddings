import json
import os
import boto3 

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
import base64

from utils import (build_response, download_folder_s3,download_file)
bedrock_client              = boto3.client("bedrock-runtime")

tmp_path                    = "/tmp"

#calls Bedrock to get a vector from either an image, text, or both
def get_multimodal_vector(input_image_base64=None, input_text=None):
    
    session = boto3.Session()

    bedrock = session.client(service_name='bedrock-runtime') #creates a Bedrock client
    
    request_body = {}
    
    if input_text:
        request_body["inputText"] = input_text
        
    if input_image_base64:
        request_body["inputImage"] = input_image_base64
    
    body = json.dumps(request_body)
    
    response = bedrock.invoke_model(
    	body=body, 
    	modelId="amazon.titan-embed-image-v1", 
    	accept="application/json", 
    	contentType="application/json"
    )
    
    response_body = json.loads(response.get('body').read())
    
    embedding = response_body.get("embedding")
    
    return embedding

#creates a vector from a file
def get_vector_from_file(file_path):
    with open(file_path, "rb") as image_file:
        input_image_base64 = base64.b64encode(image_file.read()).decode('utf8')
    
    vector = get_multimodal_vector(input_image_base64 = input_image_base64)
    
    return vector


def lambda_handler(event, context):
    print (event)
    vector_location         = event.get("vectorStoreLocation")
    vectorStore_type        = event.get("vectorStoreType")
    bucket_name             = event.get("bucketName")

    query                   = event.get("query")
    embedding_model         = event.get("embeddingModel")
    input_type              = event.get("InputType")

    query                   = query if query else ""

    
    print ("vectorStoreType:", vectorStore_type)
    print ("embeddingModel:", embedding_model)
    print ("vectorStoreLocation:",vector_location)
    print("query:",query)
    print("InputType:", input_type)


    file_name                = vector_location.split('/')[-1]
    bedrock_embeddings      = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)


    local_path = f"{tmp_path}/{file_name}"

    if not os.path.exists(local_path):
        print("archivo faiss no existe")
        download_folder_s3(bucket_name, vector_location, local_path)

    db = FAISS.load_local(local_path, bedrock_embeddings, allow_dangerous_deserialization=True)
    print("DB Done")
    if input_type == "text":
        search_vector = get_multimodal_vector(input_text=query)
        results = db.similarity_search_by_vector(embedding=search_vector)
    elif input_type == "image":
        bucket_query_path = query.split('/')[0]
        file_name         = query.split("/")[-1]
        key_query_path =  query.replace(query.split("/")[0],"").lstrip("/")
        local_file        = f"{tmp_path}/{file_name}"
        print(f"dowload from s3://{bucket_query_path}{key_query_path} to {local_file}")
        download_file(bucket_query_path,key_query_path, local_file)
        vector = get_vector_from_file(local_file)
        results = db.similarity_search_by_vector(embedding=vector)
    
    print (results)


    return build_response(200,json.dumps({"docs": [json.loads(doc.json()) for doc in results] }))

