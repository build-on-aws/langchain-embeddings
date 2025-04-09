import json
import uuid
from datetime import datetime


from aurora_service import AuroraPostgres, get_ssm_parameter
from utils import read_image_from_s3, read_json_from_s3
from transcribe_utils import (
    process_segments,
    combine_by_seconds,
    combine_transcrip_segments_by_speaker,
)
from embeddings import get_embeddings
import os


sample_event = {
    "s3_uri": "s3://bucket-name/video_in/video_corto_con_audio.mp4",
    "audio_video_processor": {
        "video_workflow": {
            "bucket": "bucket-name",
            "key": "video_in/video_corto_con_audio.mp4",
            "selected_frames": [91, 157, 164, 225],
        },
        "audio_workflow": {
            "status": "COMPLETED",
            "transcriptUrl": "https://s3.region.amazonaws.com/buecket-name/video_in/video_corto_con_audio.mp4/transcribe.json",
            "mediaUrl": "s3://bucket-name/video_in/video_corto_con_audio.mp4",
        },
    },
}


def create_frames_embeddings(frames_obj):
    frame_embeddings = []
    selected_frames = frames_obj.get("selected_frames", [])
    bucket = frames_obj.get("bucket", "")
    key = frames_obj.get("key", "")
    file = key.split("/")[-1]
    for sf in selected_frames:
        s3_uri = f"s3://{bucket}/{key}/selected_frames/{sf}.jpg"
        image_bytes = read_image_from_s3(s3_uri)
        embed = get_embeddings(image_bytes)
        frame_embeddings.append(
            {
                "embedding": embed,
                "chunks": "",
                "topic": "",
                "language": "en",
                "sourceurl": s3_uri,
                "source": file,
                "metadata": {},
                "id": str(uuid.uuid4()),
                "content_type": "image",
                "time": sf,
                "date": datetime.now().isoformat(),
            }
        )
    return frame_embeddings


def create_text_embeddings(segments, source, sourceurl):
    text_embeddings = []
    for elem in segments:
        second = elem[0]
        speaker = elem[1]
        content = elem[2]

        embed = get_embeddings(content)
        text_embeddings.append(
            {
                "embedding": embed,
                "chunks": content.replace("'", "''"),
                "topic": "",
                "language": "en",
                "sourceurl": sourceurl,
                "source": source,
                "metadata": json.dumps({"speaker": speaker}),
                "id": str(uuid.uuid4()),
                "content_type": "text",
                "time": second,
                "date": datetime.now().isoformat(),
            }
        )
    return text_embeddings


def process_transcript(audio_output):
    try:
        parts = audio_output.get("transcriptUrl").split("//")[-1].split("/", 2)
        transcription = read_json_from_s3(f"s3://{parts[1]}/{parts[2]}")
        media_s3_uri = audio_output.get("mediaUrl")

        items = transcription.get("results").get("items")
        segments, duration = process_segments(items)
        combined_by_second = combine_by_seconds(segments)
        combined_by_speaker = combine_transcrip_segments_by_speaker(combined_by_second)

        text_embeddings = create_text_embeddings(
            combined_by_speaker, media_s3_uri.split("/")[-1], media_s3_uri
        )

        return text_embeddings
    except Exception as e:
        print(f"Error processing transcript: {str(e)}")
        return []


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    try:
        # Extract information from the event
        s3_uri = event.get("s3_uri")
        audio_video_processor = event.get("audio_video_processor", {})

        video_workflow = audio_video_processor.get("video_workflow", {})
        audio_workflow = audio_video_processor.get("audio_workflow", {})

        text_embeddings = process_transcript(audio_workflow)
        frames_embeddings = create_frames_embeddings(video_workflow)

        # Get Aurora PostgreSQL connection parameters from SSM
        cluster_arn = os.environ.get("CLUSTER_ARN")
        credentials_arn = os.environ.get("SECRET_ARN")
        database_name = os.environ.get("DATABASE_NAME", "kbdata")

        # Initialize Aurora PostgreSQL client
        aurora = AuroraPostgres(cluster_arn, database_name, credentials_arn)

        # Insert text embeddings into Aurora PostgreSQL
        if text_embeddings:
            aurora.insert(text_embeddings)
            print(f"Inserted {len(text_embeddings)} text embeddings")

        # Insert frame embeddings into Aurora PostgreSQL
        if frames_embeddings:
            aurora.insert(frames_embeddings)
            print(f"Inserted {len(frames_embeddings)} frame embeddings")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Successfully processed video and audio data",
                    "s3_uri": s3_uri,
                }
            ),
        }

    except Exception as e:
        print(f"Error processing results: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Error: {str(e)}", "s3_uri": event.get("s3_uri", "")}
            ),
        }
