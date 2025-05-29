from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    Size,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3 as s3,
)

from constructs import Construct

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(900),
    memory_size=256,
    runtime=aws_lambda.Runtime.PYTHON_3_13,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)

from layers import LangchainCore


class Lambdas(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ======================================================================
        # Lambda  retriveal
        # ======================================================================

        lc_layer = LangchainCore(self, "LangchainCore")

        self.retrieval = aws_lambda.Function(
            self,
            "retrieval",
            handler="lambda_function.lambda_handler",
            layers=[lc_layer.layer],
            code=aws_lambda.Code.from_asset("./lambdas/code/retrieval"),
            **BASE_LAMBDA_CONFIG
        )

        self.retrieval.add_to_role_policy(
            iam.PolicyStatement(actions=["bedrock:*"], resources=["*"])
        )
        
        self.retrieval.add_to_role_policy(
            iam.PolicyStatement(actions=["s3:*"], resources=["*"])
        )
        self.retrieval.add_to_role_policy(
            iam.PolicyStatement(actions=["dynamodb:*"], resources=["*"])
        )
