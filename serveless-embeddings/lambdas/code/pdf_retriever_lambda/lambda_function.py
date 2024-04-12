import json
import os
import boto3 

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings

from utils import (build_response, download_folder_s3)
bedrock_client              = boto3.client("bedrock-runtime")

tmp_path                    = "/tmp"


def lambda_handler(event, context):
    print (event)
    vector_location         = event.get("vectorStoreLocation")
    vectorStore_type        = event.get("vectorStoreType")
    bucket_name             = event.get("bucketName")

    query                   = event.get("query")
    embedding_model         = event.get("embeddingModel")
    num_docs                = event.get("numDocs")

    query                   = query if query else ""
    num_docs                = num_docs if num_docs else 5
    
    print ("vectorStoreType:", vectorStore_type)
    print ("embeddingModel:", embedding_model)
    print ("vectorStoreLocation:",vector_location)
    print("query:",query)
    print("numDocs:", num_docs)


    file_name                = vector_location.split('/')[-1]

    bedrock_embeddings      = BedrockEmbeddings(model_id=embedding_model,client=bedrock_client)


    local_path = f"{tmp_path}/{file_name}"
    if not os.path.exists(local_path):
        print("archivo faiss no existe")
        download_folder_s3(bucket_name, vector_location, local_path)

    db                      = FAISS.load_local(local_path, bedrock_embeddings, allow_dangerous_deserialization=True)
    retriever               = db.as_retriever(search_kwargs = {'k':num_docs}, search_type = "mmr")
    docs                    = retriever.invoke(query)
    print (docs)
    return build_response(200,json.dumps({"docs": [json.loads(doc.json()) for doc in docs] }))

