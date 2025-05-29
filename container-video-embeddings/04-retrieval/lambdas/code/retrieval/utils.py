import json, decimal
import boto3
import os, re
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from urllib.parse import unquote

secrets_client      = boto3.client(service_name='secretsmanager')
dynamodb            = boto3.resource('dynamodb')
s3                  = boto3.client('s3')
ssm                 = boto3.client('ssm')



def get_config(secret_name):
    # Create a Secrets Manager client
    try:
        get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = None
    return secret



def read_json_from_s3(s3_uri):

    # Handle URL encoded characters in s3_uri
    
    s3_uri = unquote(s3_uri)

    parts = s3_uri.split('s3://')[-1].split('/', 1)
    bucket_name = parts[0]
    json_key = parts[1]
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=json_key)
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        return json_data
    except Exception as e:
        print(f'Error reading JSON from {s3_uri}: {str(e)}')
        raise


def read_image_from_s3(s3_key):
    parts = s3_key.split('s3://')[-1].split('/', 1)
    bucket_name = parts[0]
    image_key = parts[1]
    response = s3.get_object(Bucket=bucket_name, Key=image_key)
    image_data = response['Body'].read()
    return image_data

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
def get_item_from_table(table_name,  key_item):
        table = dynamodb.Table(table_name)
        response = table.get_item(
            Key=key_item
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
    

def update_item(table_name,id, key, value):


    table = dynamodb.Table(table_name)

    response = table.update_item(
        Key={'id': id},
        UpdateExpression=f"SET #item = :val",
        ExpressionAttributeNames={'#item': key},
        ExpressionAttributeValues={':val': value},
        ReturnValues="UPDATED_NEW"
    )
    print (response) 

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
    

def get_email(evt):
    request_context = evt.get("requestContext")
    if request_context:
        authorizer = request_context.get("authorizer")
        if authorizer:
            claims = authorizer.get("claims")
            if claims:
                return claims.get("email")
    return None


def get_saldo(table, key, value):
    response = table.query(KeyConditionExpression=Key(key).eq(value))
    return response.get("Items", [])

def replace_non_alphanumeric(string):
    """Replace non alphanumeric characters from a string"""
    
    # Use regular expression to match and replace non alphanumeric characters
    cleaned_string = re.sub(r'[^a-zA-Z0-9]', '_', string)
    
    return cleaned_string



def build_update_expression(to_update):
    attr_names = {}
    attr_values = {}
    update_expression_list = []
    for i, (key,val) in enumerate(to_update.items()):
        attr_names[f"#item{i}"] = key
        attr_values[f":val{i}"] = val

    for par in zip(attr_names.keys(), attr_values.keys()):
       update_expression_list.append(f"{par[0]} = {par[1]}")
    return attr_names, attr_values, f"SET {', '.join(update_expression_list)}"




def success_response(object_result):
    object_result["message"] = "OK"
    object_result["code"] = "SUCCESS"
    return build_response(200, json.dumps(object_result))


