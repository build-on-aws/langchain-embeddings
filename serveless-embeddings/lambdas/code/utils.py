import json
import boto3
import os
import errno

s3                  = boto3.client('s3')



def build_response(status_code, json_content):
    
    return {
        'statusCode': status_code,
        "headers": {
            "Content-Type": "text/html;charset=UTF-8",
            "charset": "UTF-8",
            "Access-Control-Allow-Origin": "*"
        },
        'body': json_content
    }



def upload_folder_s3(local_folder, bucket_name, s3_prefix):
    for subdir, dirs, files in os.walk(local_folder):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                s3.upload_fileobj(data, bucket_name, s3_prefix + full_path[len(local_folder):])


def download_file(bucket, key, filename):
    try:
        s3.download_file(bucket, key, filename)
        print("File downloaded successfully")
        return True
    except Exception as e:
        print("Error downloading file:", e)
        return False
    
def download_file_from_folder(bucket, key, filename):
    try:
        with open(filename, "wb") as data:
            s3.download_fileobj(bucket, key, data)
        print("Download file from s3://{}{}".format(bucket,key))
        return True
    except Exception as e:
        print("Error downloading file:", e)
        return False

def download_files_in_folder(bucket, folder,tmp_path):
    for obj in s3.list_objects(Bucket=bucket, Prefix=folder)['Contents']:
        print(obj["Key"], len(obj["Key"].split("/")))
        path = ""
        len_int = len(obj["Key"].split("/"))-1
        possition = 0
        for k in obj["Key"].split("/"):
            if possition == len_int:
                break
            path = path+"/"+k
            possition += 1
        path = path.lstrip("/")
        print(path)
        try:
            os.makedirs(tmp_path+path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        filename = tmp_path+ path +"/" + obj["Key"].split("/")[-1]
        download_file_from_folder(bucket, obj['Key'],filename)

def download_folder_s3(bucket_name, s3_prefix, local_folder):
    s3_objects = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/', Prefix=s3_prefix)

    for subdir in s3_objects['CommonPrefixes']:
        subfolder = subdir['Prefix'].split(f"{s3_prefix}/")[-1]
        local_path = os.path.join(local_folder, subfolder)
        if not os.path.exists(local_path):
            os.makedirs(local_path)

    s3_objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_prefix)

    for obj in s3_objects['Contents']:
        file_name = obj['Key'].split('/')[-1]
        local_file_path = os.path.join(local_folder, file_name)
        directory = os.path.dirname(local_file_path) 
        if not os.path.exists(directory):
            print(directory)
            os.makedirs(directory)
        s3.download_file(bucket_name, obj['Key'], local_file_path)
    
    print("downloaded file")
