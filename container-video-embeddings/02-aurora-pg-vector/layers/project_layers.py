import json
from constructs import Construct

from aws_cdk import (
    aws_lambda as _lambda
)



class RequestsAWSAuth(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        req_aws_auth = _lambda.LayerVersion(
            self, "RequestsAuth", code=_lambda.Code.from_asset("./layers/requests_aws_auth.zip"),
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_9, _lambda.Runtime.PYTHON_3_10, _lambda.Runtime.PYTHON_3_11, _lambda.Runtime.PYTHON_3_12], 
            description = 'Requests+aws_auth')
        self.layer = req_aws_auth
