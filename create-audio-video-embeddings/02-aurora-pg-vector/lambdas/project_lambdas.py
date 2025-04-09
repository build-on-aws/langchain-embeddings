from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    Size,
    aws_events as events,
    aws_events_targets as targets,
)

from constructs import Construct
from layers import RequestsAWSAuth

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(900),
    memory_size=256,
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)


class Lambdas(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ======================================================================
        # Lambda Crea Tablas Aurora Postgresql PGVector
        # ======================================================================

        requests = RequestsAWSAuth(self, "R")


        self.table_creator = aws_lambda.Function(
            self,
            "table_creator",
            layers=[requests.layer],
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambdas/code/table_creator"),
            **BASE_LAMBDA_CONFIG
        )
