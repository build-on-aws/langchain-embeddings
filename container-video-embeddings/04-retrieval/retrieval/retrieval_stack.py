import boto3

from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_ssm as ssm,
    aws_iam as iam,
)
from constructs import Construct
from apis import WebhookApi
from lambdas import Lambdas

class RetrievalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ssm_client = boto3.client("ssm", region_name=self.region)


        cluster_arn         = ssm_client.get_parameter(Name="/videopgvector/cluster_arn")["Parameter"]["Value"]
        secret_arn          = ssm_client.get_parameter(Name="/videopgvector/secret_arn")["Parameter"]["Value"]
        video_table_name          = ssm_client.get_parameter(Name="/videopgvector/video_table_name")["Parameter"]["Value"]

        Fn                  = Lambdas(self, "Fn")

        Fn.retrieval.add_environment(key="CLUSTER_ARN", value=cluster_arn)
        Fn.retrieval.add_environment(key="SECRET_ARN", value=secret_arn)
        Fn.retrieval.add_environment(key="DATABASE_NAME", value=video_table_name)

        Fn.retrieval.add_to_role_policy(
            iam.PolicyStatement(
                actions=["rds-data:ExecuteStatement"], resources=[cluster_arn]
            )
        )
        Fn.retrieval.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"], resources=[secret_arn]
            )
        )

        

        # ======================================================================
        # API Gateway REST API
        # ======================================================================

        Api = WebhookApi(self, "API", Fn.retrieval)

        ssm.StringParameter(
            self,
            "api-retrieve",
            parameter_name="/videopgvector/api_retrieve",
            string_value=Api.retrieve_api_url,
        )

        ssm.StringParameter( self, "lambda_retreval", 
                            parameter_name=f"/videopgvector/lambda_retreval_name", 
                            string_value=Fn.retrieval.function_name
                            ) 
        


