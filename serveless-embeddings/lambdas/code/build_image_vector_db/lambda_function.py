import os
import boto3
import json
import base64
from langchain_community.vectorstores import FAISS
from io import BytesIO
from PIL import Image

from utils import (upload_folder_s3, build_response, download_file,download_files_in_folder)


bedrock_client              = boto3.client("bedrock-runtime")

tmp_path                    = "/tmp"

s3_client = boto3.client('s3')


#calls Bedrock to get a vector from either an image, text, or both
def get_multimodal_vector(embedding_model,input_image_base64=None, input_text=None):
    
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
    	modelId=embedding_model, 
    	accept="application/json", 
    	contentType="application/json"
    )
    
    response_body = json.loads(response.get('body').read())
    
    embedding = response_body.get("embedding")
    
    return embedding

#creates a vector from a file
def get_vector_from_file(file_path,embedding_model):
    with open(file_path, "rb") as image_file:
        input_image_base64 = base64.b64encode(image_file.read()).decode('utf8')
    
    vector = get_multimodal_vector(embedding_model,input_image_base64 = input_image_base64,)
    
    return vector

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

def get_image_vectors_from_directory(path_name,embedding_model):
    items = []
    sub_1 = os.listdir(path_name)
    for n in sub_1:
        if n.endswith('.jpg'):
            file_path = os.path.join(path_name,n)
            check_size_image(file_path)
            vector = get_vector_from_file(file_path,embedding_model)
            items.append((file_path, vector))
        else:
            for n_2 in os.listdir(path_name+"/"+n):
                if n_2.endswith('.jpg'):
                    file_path = os.path.join(path_name+"/"+n, n_2)
                    check_size_image(file_path)
                    vector = get_vector_from_file(file_path,embedding_model)
                    items.append((file_path, vector))
                else:
                    print("no a .jpg file: ",n_2)

    return items

def create_vector_db(type,path_name,embedding_model):
    image_vectors = get_image_vectors_from_directory(path_name,embedding_model)
        
    text_embeddings = [("", item[1]) for item in image_vectors]
    metadatas = [{"image_path": item[0]} for item in image_vectors]
    if (type == "faiss"):
        db = FAISS.from_embeddings(
            text_embeddings=text_embeddings,
            embedding = None,
            metadatas = metadatas
        )
        print(f"Vector Database:{db.index.ntotal} docs")
    return db



def lambda_handler(event, context):
    print("event:", event)
    location                = event.get("location")
    vector_location         = event.get("vectorStoreLocation")
    bucket_name             = event.get("bucketName")
    vectorStore_type        = event.get("vectorStoreType")
    embedding_model         = event.get("embeddingModel")
    file_type               = event.get("fileType")


    file_name              = location.split("/")[-1]
    local_file             = f"{tmp_path}"

    download_files_in_folder(bucket_name, location,local_file)

    db                      = db = create_vector_db(vectorStore_type,local_file,embedding_model)
    print(f"Vector Database:{db.index.ntotal} docs")

    db_file                 = f"{tmp_path}/{file_name.split(".")[0]}.vdb"

    db.save_local(db_file)
    print(f"vectordb was saved in {db_file}")

    upload_folder_s3(db_file, bucket_name, vector_location)
  
    print(f"vectordb was uploaded in {vector_location}")
        
    return 200




