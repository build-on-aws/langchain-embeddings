import boto3
transcribe_client           = boto3.client('transcribe')


def get_transcribe_result_data(event):
    job_name = event.get('detail').get('TranscriptionJobName')  
    job_status = event.get('detail').get('TranscriptionJobStatus')
    response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    transcription_job_details = response.get('TranscriptionJob', {})
    mediaurl = response['TranscriptionJob']['Media']['MediaFileUri']
    transcriptUrl = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    return job_name, job_status,transcription_job_details, mediaurl, transcriptUrl

