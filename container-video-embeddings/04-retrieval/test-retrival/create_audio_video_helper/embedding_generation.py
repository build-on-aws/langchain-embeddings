import boto3
from datetime import datetime
import base64
import json
import uuid
from tqdm import tqdm

"""
- `get_image_embeddings()`: Generates embeddings for images using Amazon Bedrock
- `get_images_embeddings()`: Processes multiple images with progress bars
- `get_embeddings()`: Generic function that handles both text and image embedding generation
- `get_text_embeddings()`: Generates embeddings for text using Amazon Bedrock
- `create_text_embeddings()`: Creates structured embedding records for transcribed text
- `create_frames_embeddings()`: Creates structured embedding records for video frames


"""

class EmbeddingGeneration:
    def __init__(self,region_name,default_model_id,embedding_dimension):
        #self.videomanager = videomanager
        self.default_model_id = default_model_id
        self.embedding_dimension = int(embedding_dimension)
        self.bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=region_name)

    def get_image_embeddings(self,image_bytes):

        input_image = base64.b64encode(image_bytes).decode('utf8')

        body = json.dumps({"inputImage": input_image, "embeddingConfig": {"outputEmbeddingLength": self.embedding_dimension}})
        response = self.bedrock_runtime.invoke_model(
            body=body,
            modelId=self.default_model_id,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("embedding")

    def get_images_embeddings(self,images):
        embeddings = []
        
        # Create progress bar with additional information
        with tqdm(total=len(images), desc="Creating embeddings", 
                unit="img", dynamic_ncols=True) as pbar:
            for i, image_path in enumerate(images):
                with open(image_path, "rb") as image_file:
                    embeddings.append(self.get_image_embeddings(image_file.read()))
                pbar.set_postfix(file=image_path.split("/")[-1])  # Shows current frame being processed
                pbar.update(1)
                
        return embeddings

    def create_text_embeddings(self,segments, s3_uri):
        text_embeddings = []
        for (second, speaker, content) in segments:

            embed = self.get_embeddings(content)
            text_embeddings.append(
                {
                    "embedding": embed,
                    "chunks": content.replace("'", "''"),
                    "topic": "",
                    "language": "", # optionally 
                    "sourceurl": s3_uri,
                    "source": "",
                    "metadata": json.dumps({"speaker": speaker, "second": second}),
                    "id": str(uuid.uuid4()),
                    "content_type": "text",
                    "time": second,
                    "date": datetime.now().isoformat(),
                }
            )
        return text_embeddings

    def get_text_embeddings(self,text):
        body = json.dumps({"inputText": text, "embeddingConfig": {"outputEmbeddingLength": self.embedding_dimension}})
        response = self.bedrock_runtime.invoke_model(
            body=body,
            modelId=self.default_model_id,
            accept="application/json",
            contentType="application/json",
        )
        response_body = json.loads(response.get("body").read())
        return response_body.get("embedding")

    def get_embeddings(self,content):
        if isinstance(content, bytes):
            return self.get_image_embeddings(content)
        elif isinstance(content, str):
            return self.get_text_embeddings(content)
        
        """
        
    def create_frames_embeddings(self,selected_frames, s3_uri):
        frame_embeddings = []
        for (sf, image_file) in selected_frames:
            image_bytes = self.videomanager.read_image_from_local(image_file)
            embed = self.get_embeddings(image_bytes)
            frame_embeddings.append(
                {
                    "embedding": embed,
                    "chunks": "",
                    "topic": "",
                    "language": "",
                    "sourceurl": s3_uri,
                    "source": image_file,
                    "metadata": json.dumps({"second": sf}),
                    "id": str(uuid.uuid4()),
                    "content_type": "image",
                    "time": sf,
                    "date": datetime.now().isoformat(),
                }
            )
        return frame_embeddings
        


"""
