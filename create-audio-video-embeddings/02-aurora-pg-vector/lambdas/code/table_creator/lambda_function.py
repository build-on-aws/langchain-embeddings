'''Custom generic CloudFormation resource example'''

import json
import requests
import boto3
from pg_rds_api_help import PGSetup
import logging  # import logging

client = boto3.client('rds-data')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    '''Handle Lambda event from AWS'''
    # Setup alarm for remaining runtime minus a second
    # signal.alarm((context.get_remaining_time_in_millis() / 1000) - 1)
    try:
       
        logger.info('REQUEST RECEIVED: %s', event)
        logger.info('REQUEST RECEIVED: %s', context)
        if event['RequestType'] == 'Create':
            logger.info('CREATE!')
            event['PhysicalResourceId'] = 'NOT_YET'
            create(event, context)
        elif event['RequestType'] == 'Update':
            logger.info('UPDATE!')
            create(event, context)

        elif event['RequestType'] == 'Delete':
            logger.info('DELETE!')
            delete(event, context)
           
        else:
            logger.error('FAILED!')
            send_response(event, context, "FAILED",
                          {"Message": "Unexpected event received from CloudFormation"})
    except ValueError as error:
        logger.error('FAILED! ValueError: %s', error)
        send_response(event, context, "FAILED", {
            "Message": f"ValueError during processing: {error}"})
    except KeyError as error:
        print('FAILED! KeyError:', error)
        send_response(event, context, "FAILED", {
            "Message": f"KeyError during processing: {error}"})
    except Exception as error: 
        print('FAILED! Unexpected error:', error)
        send_response(event, context, "FAILED", {
            "Message": f"Unexpected exception during processing: {error}"})


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
        
        try:
            PG.setup()
            event['PhysicalResourceId'] = f"{table_name}|SETUP"
            send_response(event, context, "SUCCESS", {"Message": "Resource creation successful!"})
        except Exception as e:
            print(f"Error during PG.setup(): {str(e)}")
            send_response(event, context, "FAILED", {"Message": f"Resource creation failed: {str(e)}"})
    else:
        print("no resource properties!")


def delete(event, context):
    if 'PhysicalResourceId' in event:
        try:
            # TODO: Implement actual resource deletion logic here
            # For example:
            # table_name = event['PhysicalResourceId'].split('|')[0]
            # PG = PGSetup(...)
            # PG.delete_table(table_name)
            
            print(f"Deleting resource: {event['PhysicalResourceId']}")
            send_response(event, context, "SUCCESS", {"Message": "Resource deletion successful!"})
        except Exception as e:
            print(f"Error during resource deletion: {str(e)}")
            send_response(event, context, "FAILED", {"Message": f"Resource deletion failed: {str(e)}"})
    else:
        send_response(event, context, "FAILED", {"Message": "PhysicalResourceId not found in the event"})


def send_response(event, context, response_status, response_data):
    '''Send a resource manipulation status response to CloudFormation'''
    def create_response_body():
        return {
            "Status": response_status,
            "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
            "PhysicalResourceId": event.get('PhysicalResourceId', "NOPHYID"),
            "StackId": event['StackId'],
            "RequestId": event['RequestId'],
            "LogicalResourceId": event['LogicalResourceId'],
            "Data": response_data
        }

    response_body = json.dumps(create_response_body())
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