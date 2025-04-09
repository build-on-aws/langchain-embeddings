import boto3
import math
import requests

transcribe_client = boto3.client("transcribe")
s3 = boto3.resource("s3")


def process_part(part):
    start_time = part.get("start_time")
    if start_time is None:
        second = None
    else:
        second = math.floor(float(part.get("start_time")))

    speaker = part.get("speaker_label")
    content = part.get("alternatives")[0].get("content")
    return second, speaker, content


def process_segments(parts):
    all_segments = [process_part(part) for part in parts]

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


def combine_by_seconds(segments):
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


def combine_transcrip_segments_by_speaker(transcript):
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
                    and (len(current_content) > 1000)
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


def get_transcribe_result_data(event):
    job_name = event.get("detail").get("TranscriptionJobName")
    job_status = event.get("detail").get("TranscriptionJobStatus")
    response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    transcription_job_details = response.get("TranscriptionJob", {})
    mediaurl = response["TranscriptionJob"]["Media"]["MediaFileUri"]
    return job_name, job_status, transcription_job_details, mediaurl


def get_transcript_url(job_name):
    response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    mediaurl = response["TranscriptionJob"]["Media"]["MediaFileUri"]
    parts = mediaurl.split("s3://")
    bucket = parts[1].split("/")[0]
    key = "/".join(parts[1].split("/")[1:])
    print(bucket, key)
    obj = s3.Object(bucket, key)
    size = round(obj.content_length / (1024 * 1024), 1)

    transcript_url = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]

    return transcript_url, size


def get_transcript_contents(transcript_url):
    try:
        r = requests.get(transcript_url)
        r.raise_for_status()
        result = r.json()
        return result
    except requests.RequestException as e:
        print(f"Network error occurred: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}")
        return None
