import json, decimal
import boto3
import os
from botocore.exceptions import ClientError

secrets_client      = boto3.client(service_name='secretsmanager')
dynamodb            = boto3.resource('dynamodb')
s3                  = boto3.client('s3')
ssm                 = boto3.client('ssm')


def get_config_param(parameter_name):
    response = ssm.get_parameter(Name=parameter_name)
    parameter = response.get('Parameter')
    if parameter:
        return json.loads(parameter.get('Value'))
    else:
        return None
    

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

# get the whole item from table_name
from boto3.dynamodb.conditions import Key  # import boto3.dynamodb.conditions

def get_item_from_table(table_name, key_item):
    table = dynamodb.Table(table_name)
    response = table.get_item(
        Key={k: Key(k).eq(v) for k, v in key_item.items()}
    )
    return response.get('Item')



def upload_folder_s3(local_folder, bucket_name, s3_prefix):
    for subdir, dirs, files in os.walk(local_folder):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                s3.upload_fileobj(data, bucket_name, s3_prefix + full_path[len(local_folder):])



def download_file(bucket, key, filename):
    # first check if filename exists
    if os.path.exists(filename):
        print("File already exists")
        return True
    try:
        s3.download_file(bucket, key, filename)
        print("File downloaded successfully")
        return True
    except Exception as e:
        print("Error downloading file:", e)
        return False
    
def upload_file(bucket, key, filename):
    try:
        s3.upload_file(filename, bucket, key)
        print("File uploaded successfully")
        return True
    except Exception as e:
        print("Error uploading file:", e)
        return False
    

def update_item(table_name, id, key, value):
    from boto3.dynamodb.conditions import Attr  # import boto3.dynamodb.conditions

    table = dynamodb.Table(table_name)

    response = table.update_item(
        Key={'id': Attr('id').eq(id)},
        UpdateExpression="SET #item = :val",
        ExpressionAttributeNames={'#item': key},
        ExpressionAttributeValues={':val': value},
        ReturnValues="UPDATED_NEW"
    )
    print(response)

class DecimalEncoder(json.JSONEncoder):
   def default(self, obj):
      if isinstance(obj, decimal.Decimal):
         return str(obj)
      return super().default(obj)
   


def call_lambda(lambda_name, payload, invocation_type):
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=lambda_name,
        InvocationType=invocation_type,
        Payload=json.dumps(payload, cls=DecimalEncoder)
    )
    function_response = response['Payload'].read().decode("utf-8")
    if invocation_type == 'RequestResponse':
        query_string_response = json.loads(function_response)['body']
        result = json.loads(query_string_response)
        return result
    else:
        return function_response
    


def parse_location(s3_uri):
    [_, part] = s3_uri.split("s3://")
    elements = part.split("/")
    bucket = elements[0]
    prefix = "/".join(elements[1:-1])
    file = elements[-1]
    [fileName, extension] = file.split(".")
    return bucket, prefix, fileName, extension, file