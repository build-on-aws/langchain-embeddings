
from aws_cdk import (
    Duration,
    aws_iam as iam, 
    aws_lambda,

)

from constructs import Construct
from layers import RequestsAWSAuth
LAMBDA_TIMEOUT= 900

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    architecture=aws_lambda.Architecture.ARM_64,
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    tracing= aws_lambda.Tracing.ACTIVE)


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        requests = RequestsAWSAuth(self, "R")

        self.table_creator = aws_lambda.Function(
            self,
            "table_creator",
            layers=[requests.layer],
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/table_creator"),
            **BASE_LAMBDA_CONFIG
        )



        self.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["iam:PassRole"], resources=["*"]))