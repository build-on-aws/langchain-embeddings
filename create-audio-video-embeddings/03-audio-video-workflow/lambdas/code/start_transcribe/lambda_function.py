import boto3
import uuid
import os

transcribe_client = boto3.client('transcribe')

TRANSCRIBE_TABLE_NAME = os.environ.get("TRANSCRIBE_TABLE")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

transcribe_table = boto3.resource('dynamodb').Table(TRANSCRIBE_TABLE_NAME)


def parse_location(s3_uri):
    [_, part] = s3_uri.split("s3://")
    elements = part.split("/")
    bucket = elements[0]
    prefix = "/".join(elements[1:-1])
    file = elements[-1]
    [fileName, extension] = file.split(".")
    return bucket, prefix, fileName, extension, file

def lambda_handler(event, context):
    print(event)
    s3_uri = event.get("s3_uri")
    job_name = str(uuid.uuid4())
    sftoken = event.get("sftoken")

    bucket, prefix, fileName, extension, file = parse_location(s3_uri)

    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        IdentifyLanguage=True, 
        OutputBucketName=BUCKET_NAME,
        OutputKey=f"{prefix}/{file}/transcribe.json",
        Media={'MediaFileUri': s3_uri},
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 10
        }
    )

    transcription_job_name = response['TranscriptionJob']['TranscriptionJobName']
    Transcription_job_status = response['TranscriptionJob']['TranscriptionJobStatus']
    
    transcribe_table.put_item(
        Item={
            "TranscriptionJobName": transcription_job_name,
            "status": Transcription_job_status,
            "s3_uri": s3_uri,
            "sftoken": sftoken
        }
    )

    return {"job_name": transcription_job_name}
