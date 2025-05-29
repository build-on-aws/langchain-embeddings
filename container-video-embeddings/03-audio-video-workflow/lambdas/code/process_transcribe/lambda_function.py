import os
import boto3

from dynamodb_utils import update_item
from transcribe_utils import ( get_transcribe_result_data)

from step_function_utils import send_task_success, send_task_failure

transcribe_client = boto3.client("transcribe")
s3 = boto3.resource("s3")

dynamodb = boto3.resource("dynamodb")

TRANSCRIBE_TABLE_NAME = os.environ.get("TRANSCRIBE_TABLE")
transcribe_table = dynamodb.Table(TRANSCRIBE_TABLE_NAME)


def lambda_handler(event, context):
    print(event)
    job_name, job_status, transcription_job_details, mediaurl, transcripturl = get_transcribe_result_data(event)

    print (transcription_job_details)



    to_update = {
        "status": job_status,
        "transcriptUrl": transcripturl,
        "mediaUrl": mediaurl
    }
    updated_item = update_item(transcribe_table,{"TranscriptionJobName": job_name}, to_update )        
    sftoken = updated_item.get("sftoken")

    print("Sending Task Signal...")

    if job_status == "COMPLETED":
        print(f"Job {job_name} completed successfully.")
        send_task_success(sftoken, to_update)
    else:
        print(f"Job {job_name} did not complete successfully. Status: {job_status}")
        send_task_failure(sftoken, error_message=f"Job did not complete successfully. Status: {job_status}")







    
