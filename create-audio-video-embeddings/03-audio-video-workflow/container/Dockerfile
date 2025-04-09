# Using slim base image to reduce size and potential compatibility issues
FROM public.ecr.aws/docker/library/python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ADD .  /app
RUN pip3 install -r requirements.txt
CMD ["python3", "lambda_function.py"]
