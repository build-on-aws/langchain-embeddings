'''Custom generic CloudFormation resource example'''

import json
import requests
import boto3
from pg_rds_api_help import PGSetup


client = boto3.client('rds-data')

def lambda_handler(event, context):
    '''Handle Lambda event from AWS'''
    # Setup alarm for remaining runtime minus a second
    # signal.alarm((context.get_remaining_time_in_millis() / 1000) - 1)
    try:
       
        print('REQUEST RECEIVED:', event)
        print('REQUEST RECEIVED:', context)
        if event['RequestType'] == 'Create':
            print('CREATE!')
            event['PhysicalResourceId'] = 'NOT_YET'
            create(event, context)
        elif event['RequestType'] == 'Update':
            print('UPDATE!')
            create(event, context)

        elif event['RequestType'] == 'Delete':
            print('DELETE!')
            delete(event, context)
           
        else:
            print('FAILED!')
            send_response(event, context, "FAILED",
                          {"Message": "Unexpected event received from CloudFormation"})
    except Exception as error: 
        print('FAILED!', error)
        send_response(event, context, "FAILED", {
            "Message": "Exception during processing"})


def create(event, context):
    
    if "ResourceProperties" in event:
        print ("create_datasource")
        props = event['ResourceProperties']
        cluster_arn=props['cluster_arn']
        table_name = props['table_name']
        database_name=props['database_name']
        secrets_arn = props['secrets_arn']
        credentials_arn = props['credentials_arn']
        
        PG = PGSetup(
            client=client,
            cluster_arn=cluster_arn,
            secrets_arn=secrets_arn,
            database_name=database_name,
            table_name = table_name,
            credentials_arn= credentials_arn
        )        
        
        PG.setup()

        event['PhysicalResourceId'] = f"{table_name}|SETUP"
        send_response(event, context, "SUCCESS",{"Message": "Resource creation successful!"})
    else:
        print("no resource properties!")


def delete (event, context):
    if 'PhysicalResourceId' in event:
        send_response(event, context, "SUCCESS", {"Message": "Resource deletion successful!"})


def send_response(event, context, response_status, response_data):
    '''Send a resource manipulation status response to CloudFormation'''
    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": event['PhysicalResourceId'] if 'PhysicalResourceId' in event else "NOPHYID",
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })
    headers = {
    'Content-Type': 'application/json',  
    'Content-Length': str(len(response_body))
    } 


    print('ResponseURL: ', event['ResponseURL'])
    print('ResponseBody:', response_body)

    response = requests.put(event['ResponseURL'], 
                            data=response_body, headers=headers)
    
    print("Status code:", response.status_code)
    print("Status message:", response.text)

    return response


def timeout_handler(_signal, _frame):
    '''Handle SIGALRM'''
    raise Exception('Time exceeded')

# signal.signal(signal.SIGALRM, timeout_handler)