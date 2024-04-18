"""
EVENT
{
    "location": "YOU-KEY",
    "collectioName": "YOU-COLLECTION-NAME",
    "bucketName": "YOU-BUCKET",
    "fileType": "image or pdf",
    "embeddingModel": "amazon.titan-embed-image-v1", 
    "llmModel": "anthropic.claude-3-sonnet-20240229-v1:0",
    "PGVECTOR_USER":"PGVECTOR_USER",
    "PGVECTOR_PASSWORD":"PGVECTOR_PASSWORD",
    "PGVECTOR_HOST":"PGVECTOR_HOST",
    "PGVECTOR_DATABASE":"PGVECTOR_DATABASE"
  }
"""

import os
import boto3
import json
import base64
import os
from PIL import Image

from sqlalchemy import create_engine
from langchain_community.embeddings import BedrockEmbeddings # to create embeddings for the documents.
from langchain_experimental.text_splitter import SemanticChunker # to split documents into smaller chunks.
from langchain.docstore.document import Document
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from langchain_community.document_loaders import PyPDFLoader


from utils import (build_response, download_file)

tmp_path                    = "/tmp"

bedrock_client              = boto3.client("bedrock-runtime") 


# function to create vector store
def create_vectorstore(embeddings,collection_name,conn):
                       
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=conn,
        use_jsonb=True,
    )
    return vectorstore

def load_and_split_pdf_semantic(file_path, embeddings):
    text_splitter = SemanticChunker(embeddings, breakpoint_threshold_amount= 80)
    loader = PyPDFLoader(file_path)
    docs = loader.load_and_split(text_splitter)
    print(f"docs:{len(docs)}")
    return docs

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

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    vector = get_multimodal_vector(input_image_base64=encoded_string)
    return encoded_string, vector

def check_size_image(file_path):
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

def get_image_vectors_from_directory(path_name):
    documents = []
    embeddings = []
    for folder in os.walk(path_name):
        #print(f'In {folder[0]} are {len(folder[2])} folder:')
        for fichero in folder[2]:
            if fichero.endswith('.jpg'):
                file_path = os.path.join(folder[0], fichero)
                #print(file_path)
                check_size_image(file_path)
                image_base64, image_embedding = image_to_base64(file_path)
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

    user = event.get("PGVECTOR_USER")
    password = event.get("PGVECTOR_PASSWORD")
    host = event.get("PGVECTOR_HOST")
    database = event.get("PGVECTOR_DATABASE")

    # Create the SQLAlchemy engine
    engine = create_engine(f"postgresql://{user}:{password}@{host}/{database}") 
    
    file_name              = location.split("/")[-1]
    local_file             = f"{tmp_path}/{file_name}"

    print(f"dowload from s3://{bucket_name}{location} to {local_file}")
    download_file(bucket_name,location, local_file)

    bedrock_embeddings          = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)

    if file_type == "pdf":
        docs = load_and_split_pdf_semantic(local_file, bedrock_embeddings)
        vectorstore = create_vectorstore(bedrock_embeddings,collection_name,engine)
        # Add documents to the vectorstore
        vectorstore.add_documents(docs)
        print(f"Vector Database Done:{vectorstore.index.ntotal} docs")

    elif file_type == "image":
        documents, embeddings = get_image_vectors_from_directory(local_file)
        image_vectorstore = create_vectorstore(bedrock_embeddings,collection_name,engine)
        texts = [d.get("file_path") for d in documents]
        metadata = [{"file_path": d.get("file_path")} for d in documents]
        image_vectorstore.add_embeddings(embeddings=embeddings, texts=texts, metadata=metadata)
        print(f"Vector Database Done:{image_vectorstore.index.ntotal} docs")

    return build_response(200, json.dumps(event))

    




