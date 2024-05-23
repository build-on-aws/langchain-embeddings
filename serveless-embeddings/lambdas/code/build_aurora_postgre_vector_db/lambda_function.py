"""
EVENT
{
    "location": "YOU-KEY",
    "bucketName": "YOU-BUCKET-NAME",
    "fileType": "pdf or image",
    "embeddingModel": "amazon.titan-embed-text-v1", 
    "PGVECTOR_USER":"YOU-PGVECTOR_USER,
    "PGVECTOR_PASSWORD":"YOU-PGVECTOR_PASSWORD",
    "PGVECTOR_HOST":"YOU-PGVECTOR_HOST",
    "PGVECTOR_DATABASE":"YOU-PGVECTOR_DATABASE"
    "PGVECTOR_PORT":"5432",
    "collectioName": "YOU-collectioName"
  }
"""

import os
import boto3
import json
import base64
import os
from PIL import Image
import psycopg

from langchain_community.embeddings import BedrockEmbeddings # to create embeddings for the documents.
from langchain_experimental.text_splitter import SemanticChunker # to split documents into smaller chunks.
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_community.document_loaders import PyPDFLoader

from utils import (download_file,    download_files_in_folder)

tmp_path                    = "/tmp"




# function to create vector store
def create_vectorstore(embeddings,collection_name,conn):
    print(f"creating vectorstore for {collection_name}")
                    
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=conn,
        use_jsonb=True,
    )
    return vectorstore

def load_and_split_pdf_semantic(file_path, embeddings):
    print(f"loading and splitting pdf: {file_path}")
    text_splitter = SemanticChunker(embeddings, breakpoint_threshold_amount= 80)
    print(f"text_splitter")
    loader = PyPDFLoader(file_path)
    print(f"loader")
    docs = loader.load_and_split(text_splitter)
    print(f"docs:{len(docs)}")
    return docs

#calls Bedrock to get a vector from either an image, text, or both
def get_multimodal_vector(bedrock_client,input_image_base64=None, input_text=None):
    print(f"get_multimodal_vector")
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

def image_to_base64(image_path,bedrock_client):
    print(f"image_to_base64 image_path:{image_path}")
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    vector = get_multimodal_vector(bedrock_client,input_image_base64=encoded_string)
    return encoded_string, vector

def check_size_image(file_path):
    print(f"check_size_image file_path:{file_path}")
    # Maximum image size supported is 2048 x 2048 pixel
    image = Image.open(file_path) #open image
    width, height = image.size # Get the width and height of the image in pixels
    if width > 2048 or height > 2048:
        print(f"Big File:{file_path} , width: {width}, height {height} px")
        dif_width = width - 2048
        dif_height = height - 2048
        if dif_width > dif_height:
            ave = 1-(dif_width/width)
            new_width = int(width*ave)
            new_height = int(height*ave)
        else:
            ave = 1-(dif_height/height)
            new_width = int(width*ave)
            new_height = int(height*ave)
        print(f"New file: {file_path} , width: {new_width}, height {new_height} px")

        new_image = image.resize((new_width, new_height))
        # Save New image
        new_image.save(file_path)
 
    return

def get_image_vectors_from_directory(path_name,bedrock_client):
    print(f"get_image_vectors_from_directory:{path_name}")
    documents = []
    embeddings = []

    for folder in os.walk(path_name):
        #print(f'In {folder[0]} are {len(folder[2])} folder:')
        for fichero in folder[2]:
            if fichero.endswith('.jpg'):
                file_path = os.path.join(folder[0], fichero)
                #print(file_path)
                check_size_image(file_path)
                image_base64, image_embedding = image_to_base64(file_path,bedrock_client)
                documents.append({"page_content": image_base64, "file_path": file_path})
                embeddings.append(image_embedding)
            else:
                print("no a .jpg file: ", fichero)

    return documents, embeddings

def lambda_handler(event, context):
    print("event:", event)

    location                = event.get("location")
    collection_name         = event.get("collectioName")
    bucket_name             = event.get("bucketName")
    file_type               = event.get("fileType")
    embedding_model         = event.get("embeddingModel")
    bedrock_endpoint = event.get("bedrockEndpoint")
     

    user = event.get("PGVECTOR_USER")
    password = event.get("PGVECTOR_PASSWORD")
    host = event.get("PGVECTOR_HOST")
    database = event.get("PGVECTOR_DATABASE")
    port = event.get("PGVECTOR_PORT")

    connection = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}" 
    print(f"connection:{connection}")
    file_name              = location.split("/")[-1]
    local_file             = f"{tmp_path}/{file_name}"

    if bedrock_endpoint : 
        bedrock_client = boto3.client("bedrock-runtime", endpoint_url = bedrock_endpoint) # If the lambda function is inside a VPC
    else: 
        bedrock_client = boto3.client("bedrock-runtime")


    bedrock_embeddings          = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)

    conn = psycopg.connect(
                   conninfo = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                       )
    #Create a cursor to run queries
    cur = conn.cursor()

    value_cur = cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    print(value_cur)

    if file_type == "pdf":
        print(f"Is pdf file" )
        print(f"dowload from s3://{bucket_name}/{location} to {local_file}")
        download_file(bucket_name,location, local_file)
        vectorstore = create_vectorstore(bedrock_embeddings,collection_name,connection)
        print("To create docs")
        docs = load_and_split_pdf_semantic(local_file, bedrock_embeddings)
        # Add documents to the vectorstore
        vectorstore.add_documents(docs)
        print(f"Vector Database Done:{vectorstore} docs")

    elif file_type == "image":
        print(f"Is image file" )
        print(f"dowload from s3://{bucket_name}/{location} to {local_file}")
        download_files_in_folder(bucket_name, location,local_file)
        vectorstore = create_vectorstore(bedrock_embeddings,collection_name,connection)
        documents, embeddings = get_image_vectors_from_directory(local_file,bedrock_client)
        texts = [d.get("file_path") for d in documents]
        metadata = [{"file_path": d.get("file_path")} for d in documents]
        print("To create docs")
        vectorstore.add_embeddings(embeddings=embeddings, texts=texts, metadata=metadata)
        print(f"Vector Database Done:{vectorstore} docs")
    print(f"Event done")
    return 200

    




