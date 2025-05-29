import boto3
from datetime import datetime
import math
import time

"""
Implements functions for:
- `transcribe()`: Starts transcription jobs with Amazon Transcribe
- `wait_transcription_complete()`: Waits for job completion with status polling
- `get_transcribe_result_data()`: Gets transcription job status and results
- `process_part()`: Processes individual parts of the transcript
- `process_segments()`: Processes transcript segments with timing information
- `combine_by_seconds()`: Combines transcript segments by time
- `combine_transcrip_segments_by_speaker()`: Combines segments by speaker for better readability
- `process_transcript()`: Main function to process the complete transcript
"""

class AudioProcessing:
    def __init__(self,region_name,videomanager):
        self.videomanager = videomanager
        self.transcribe_client = boto3.client(service_name='transcribe',region_name=region_name)

    def transcribe(self, s3_uri, job_name=None):
        
        bucket, prefix, fileName, extension, file  = self.videomanager.parse_location(s3_uri)

        if not job_name:
                timestamp = datetime.now().strftime('%y%m%d-%H%M%S')
                job_name = s3_uri.split('/')[-1]
                # Add timestamp suffix to job_name
                job_name = f"{job_name}-{timestamp}"

        try:

            response = self.transcribe_client.start_transcription_job(
                    TranscriptionJobName=job_name,
                    IdentifyLanguage=True, 
                    OutputBucketName = bucket,
                    OutputKey = f"{prefix}/{file}/transcribe.json",
                    Media={ 'MediaFileUri': s3_uri},
                    Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 10
                })
            job_name = response['TranscriptionJob']['TranscriptionJobName']
            print(f"Transcription job {job_name} started...")
            return job_name

        except Exception as e:
            print(e)
            return None
        
    def wait_transcription_complete(self,job_name):
        while True:
            job_status, transcriptUrl = self.get_transcribe_result_data(job_name)
            if job_status in ['COMPLETED', 'FAILED']: break
            print(f"Transcription job {job_name} is {job_status}...")
            time.sleep(10)
        print(f"Transcription job {job_name} is {job_status}...")
        return transcriptUrl

    def get_transcribe_result_data(self,job_name):
        response = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        transcription_job_details = response.get('TranscriptionJob', {})
        job_status = transcription_job_details.get('TranscriptionJobStatus')
        transcriptUrl = transcription_job_details.get('Transcript',{}).get('TranscriptFileUri')
        return job_status, transcriptUrl


    def process_part(self,part):
        start_time = part.get("start_time")
        if start_time is None:
            second = None
        else:
            second = math.floor(float(part.get("start_time")))

        speaker = part.get("speaker_label")
        content = part.get("alternatives")[0].get("content")
        return second, speaker, content


    def process_segments(self,parts):
        all_segments = [self.process_part(part) for part in parts]

        destilled_segments = []
        current_time, current_speaker, current_content = all_segments[0]
        for start_time, speaker, content in all_segments[1:]:
            if speaker == current_speaker:
                if start_time is None:
                    current_content += f" {content}"
                else:
                    destilled_segments.append(
                            (current_time, current_speaker, current_content)
                        )
                    current_time, current_speaker, current_content = (
                            start_time,
                            speaker,
                            content,
                        )
            else:
                current_time, current_speaker, current_content = (
                        start_time,
                        speaker,
                        content,
                    )

        destilled_segments.append((current_time, current_speaker, current_content))
        ending_times = [
                p.get("end_time") for p in parts if p.get("type") == "pronunciation"
            ]
        return destilled_segments, ending_times[-1]

    def combine_by_seconds(self, segments):
        combined = []
        current_time, current_speaker, current_content = segments[0]
        for start_time, speaker, content in segments[1:]:
            if start_time == current_time:
                if speaker == current_speaker:
                    current_content += f" {content}"
                else:
                    combined.append((current_time, current_speaker, current_content))
                    current_time, current_speaker, current_content = (
                        start_time,
                        speaker,
                        content,
                    )
            else:
                combined.append((current_time, current_speaker, current_content))
                current_time, current_speaker, current_content = (
                    start_time,
                    speaker,
                    content,
                )

        combined.append((current_time, current_speaker, current_content))
        return combined


    def combine_transcrip_segments_by_speaker(self,transcript, max_chars_per_segment):
        combined = []
        current_speaker = None
        current_content = ""
        current_second = None
        for second, speaker, content in transcript:
            if "spk_" in speaker:
                if current_speaker is None:
                    current_speaker = speaker
                    current_content = content
                    current_second = second
                    continue

                if speaker == current_speaker:
                    current_content = current_content + " " + content

                    if (
                        content.rstrip().endswith((".", "!", "?"))
                        and (len(current_content) > max_chars_per_segment)
                    ):
                        combined.append((current_second, current_speaker, current_content))
                        current_speaker = speaker
                        current_content = content
                        current_second = second
                else:
                    combined.append((current_second, current_speaker, current_content))
                    current_speaker = speaker
                    current_content = content
                    current_second = second
        if (len(current_content) < 100) and (len(combined) > 1):
            last_elem = combined.pop()
            combined.append((last_elem[0], last_elem[1], last_elem[2]+current_content))
            return combined

        combined.append((current_second, current_speaker, current_content))
        return combined


    def process_transcript(self,transcriptUrl, max_chars_per_segment = 1000):

        parts = transcriptUrl.split("//")[-1].split("/", 2)
        transcription = self.videomanager.read_json_from_s3(f"s3://{parts[1]}/{parts[2]}")
        items = transcription.get("results").get("items")
        segments, duration = self.process_segments(items)
        combined_by_second = self.combine_by_seconds(segments)
        combined_by_speaker = self.combine_transcrip_segments_by_speaker(combined_by_second, max_chars_per_segment)
        return combined_by_speaker, duration