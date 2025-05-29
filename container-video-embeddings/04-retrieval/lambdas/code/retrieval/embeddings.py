import boto3
import base64
import json
import os


bedrock_runtime = boto3.client(service_name="bedrock-runtime")

# Default model settings
default_model_id = os.environ.get("DEFAULT_MODEL_ID", "amazon.titan-embed-image-v1")
default_embedding_dimension = os.environ.get("DEFAULT_EMBEDDING_DIMENSION", "1024")

def get_image_embeddings(image_bytes, model_id=default_model_id, embedding_dimension=int(default_embedding_dimension)):
    input_image = base64.b64encode(image_bytes).decode('utf8')
    print("Getting image embeddings")

    body = json.dumps({"inputImage": input_image, "embeddingConfig": {"outputEmbeddingLength": embedding_dimension}})
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_id,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")


def get_text_embeddings(text, model_id=default_model_id, embedding_dimension=int(default_embedding_dimension)):
    body = json.dumps({"inputText": text, "embeddingConfig": {"outputEmbeddingLength": embedding_dimension}})
    print("Getting text embeddings")
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_id,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")


def get_embeddings(content, model_id=default_model_id, embedding_dimension=int(default_embedding_dimension)):
    if isinstance(content, bytes):
        return get_image_embeddings(content, model_id, embedding_dimension)
    elif isinstance(content, str):
        return get_text_embeddings(content, model_id, embedding_dimension)