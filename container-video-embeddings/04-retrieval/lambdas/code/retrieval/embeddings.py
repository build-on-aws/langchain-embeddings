import boto3
import base64
import json
import os


bedrock_runtime = boto3.client(service_name="bedrock-runtime")

# Default model settings
default_model_id = os.environ.get("DEFAULT_MODEL_ID", "amazon.nova-2-multimodal-embeddings-v1:0")
default_embedding_dimension = os.environ.get("DEFAULT_EMBEDDING_DIMENSION", "1024")

def get_image_embeddings(image_bytes, model_id=default_model_id, embedding_dimension=int(default_embedding_dimension)):
    input_image = base64.b64encode(image_bytes).decode('utf8')
    print("Getting image embeddings")

    body = json.dumps({
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": embedding_dimension,
            "image": {"format": "jpeg", "source": {"bytes": input_image}},
        },
    })
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_id,
        accept="application/json",
        contentType="application/json",
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")


def get_text_embeddings(text, model_id=default_model_id, embedding_dimension=int(default_embedding_dimension)):
    body = json.dumps({
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": embedding_dimension,
            "text": {"value": text, "truncationMode": "END"},
        },
    })
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