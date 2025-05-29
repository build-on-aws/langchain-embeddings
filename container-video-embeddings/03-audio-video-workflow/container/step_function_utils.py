import json, decimal
import boto3

sf = boto3.client("stepfunctions")

class DecimalEncoder(json.JSONEncoder):
   def default(self, obj):
      if isinstance(obj, decimal.Decimal):
         return str(obj)
      return super().default(obj)



def send_task_success(token, output):
    params = {"taskToken": token, "output": json.dumps(output, cls=DecimalEncoder)}
    return sf.send_task_success(**params)


def send_task_failure(token, error_code="TaskFailure", error_message="Task execution failed"):
    """
    Report a task failure to AWS Step Functions.
    
    Args:
        token (str): The task token that was provided in the task input
        error_code (str): A custom error code to identify the error type
        error_message (str): A detailed error message describing what went wrong
        
    Returns:
        The response from the Step Functions service
    """
    params = {
        "taskToken": token,
        "error": error_code,
        "cause": error_message
    }
    return sf.send_task_failure(**params)