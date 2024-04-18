"""
EVENT
{
    "location": "YOU-KEY",
    "vectorStoreLocation": "NAME.vdb",
    "bucketName": "YOU-BUCKET",
    "vectorStoreType": "faiss",
    "splitStrategy": "semantic",
    "fileType": "application/pdf", 
    "embeddingModel": "amazon.titan-embed-text-v1"
  }
"""

import json
import os
import boto3 

from langchain_community.document_loaders import PyPDFLoader

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

from utils import (upload_folder_s3, build_response, download_file)


bedrock_client              = boto3.client("bedrock-runtime")

tmp_path                    = "/tmp"




def load_and_split_pdf_semantic(file_path, embeddings):
    text_splitter           = SemanticChunker(embeddings, breakpoint_threshold_amount= 80)
    loader                  = PyPDFLoader(file_path)
    docs                    = loader.load_and_split(text_splitter)
    return docs


def load_and_split_semantic(file_type, file_path, embeddings):
    if file_type == "application/pdf":
        docs = load_and_split_pdf_semantic(file_path, embeddings)  
    clean_docs = []
    for doc in docs:
        if len(doc.page_content):
            clean_docs.append(doc)
    print(f"docs:{len(clean_docs)}")
    return clean_docs

def create_vector_store(type, docs, embeddings):
    if (type == "faiss") and docs:
        return FAISS.from_documents(docs, embeddings)
    return None

def lambda_handler(event, context):
    print("event:", event)
    location                = event.get("location")
    vector_location         = event.get("vectorStoreLocation")
    bucket_name             = event.get("bucketName")
    vectorStore_type        = event.get("vectorStoreType")
    split_strategy          = event.get("splitStrategy")
    embedding_model         = event.get("embeddingModel")
    file_type               = event.get("fileType")

    if split_strategy == "recursive":
        chunk_size              = event.get("chunkSize") if event.get("chunkSize") else 1000
        chunk_overlap           = event.get("chunkOverlap") if event.get("chunkOverlap") else 100

    file_name              = location.split("/")[-1]
    local_file             = f"{tmp_path}/{file_name}"

    print(f"dowload from s3://{bucket_name}{location} to {local_file}")
    download_file(bucket_name,location, local_file)

    bedrock_embeddings      = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)

    if split_strategy  == "semantic":
        docs = load_and_split_semantic(file_type, local_file, bedrock_embeddings)
    

    db                      = create_vector_store(vectorStore_type, docs, bedrock_embeddings)
    print(f"Vector Database:{db.index.ntotal} docs")

    db_file                 = f"{tmp_path}/{file_name.split(".")[0]}.vdb"

    event['size'] = db.index.ntotal


    db.save_local(db_file)
    print(f"vectordb was saved in {db_file}")

    upload_folder_s3(db_file, bucket_name, vector_location)
  
    print(f"vectordb was uploaded in {vector_location}")

        
    return build_response(200, json.dumps(event))




