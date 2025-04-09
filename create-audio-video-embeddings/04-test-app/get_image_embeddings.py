import json
import base64
import boto3
import os

bedrock_runtime = boto3.client(service_name="bedrock-runtime")
default_model_id = os.environ.get("DEFAULT_MODEL_ID", "amazon.titan-embed-image-v1")
default_embedding_dimmesion = os.environ.get("DEFAULT_EMBEDDING_DIMENSION", "1024")


def get_image_embeddings(path_to_image, model_id:str = default_model_id, embedding_dimmesion = int(default_embedding_dimmesion)):
    

    with open(path_to_image, "rb") as image_file:
        input_image = base64.b64encode(image_file.read()).decode('utf8')

    body = json.dumps({"inputImage": input_image,"embeddingConfig": { "outputEmbeddingLength": embedding_dimmesion}})


    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_id,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")


def get_images_embeddings(images, model_id:str = default_model_id, embedding_dimmesion = int(default_embedding_dimmesion)):
    embeddings = []
    print ("starting embedding process...")

    for index, image in enumerate(images):
        print (index, end=" ")
        embeddings.append(get_image_embeddings(image, model_id, embedding_dimmesion))
    return embeddings
