import os
import sys
from step_function_utils import send_task_success, send_task_failure
from video_processor import ffmpeg_check, extract_frames
from utils import download_file, parse_location, upload_file
from get_image_embeddings import get_images_embeddings
from similarity import cosine_similarity_list, filter_relevant_frames

tmp_path                    = "./tmp"
difference_threshold        = 0.9

if __name__ == "__main__":

    s3_uri = os.environ.get("S3_URI", "s3://bucket/key")
    task_token = os.environ.get("TASK_TOKEN", None)

    try:
        # Check if ffmpeg is installed
        ffmpeg_check()

        # Parse the S3 URI
        bucket, prefix, fileName, extension, file  = parse_location(s3_uri)

        # Print bucket and key
        print(f"Bucket: {bucket}")
        print(f"prefix: {prefix}")
        print(f"extension: {extension}")
        print(f"file: {file}")

        local_path              = f"{tmp_path}/{file}"
        location                = f"{prefix}/{file}"
        output_dir              = f"{tmp_path}/{fileName}"


        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        print(f"descargando {file} s3://{bucket}/{prefix} to {local_path}")
        download_file(bucket,location, local_path)

        files = extract_frames(local_path, output_dir)
        embed_1024 = get_images_embeddings(files, embedding_dimmesion=1024)
        similarity_1024 = cosine_similarity_list(embed_1024)
        similarity_1024.append(0.5) # add this so the last one is pick
        selected_frames = filter_relevant_frames( similarity_1024, difference_threshold = difference_threshold)

        selected_frames_real = []


        for sf in selected_frames:

            origen_file = f"{output_dir}/sec_{str(sf+1).zfill(5)}.jpg"
            real_frame = sf + 1
            destination_key = f"{prefix}/{file}/selected_frames/{real_frame}.jpg"

            print(f"{origen_file} => {destination_key}")
            upload_file(bucket, destination_key, origen_file)
            selected_frames_real.append(real_frame)


        if task_token:
            print("Task Token: [REDACTED]")
            send_task_success(task_token, {
                "bucket": bucket,
                "key": f"{prefix}/{file}",
                "selected_frames": selected_frames_real
            })


    except Exception as e:
        print(f"Error: {str(e)}")
        if task_token: send_task_failure(task_token, error_message=str(e))
        sys.exit(1)
