import sys
import json

from aws_cdk import (
    Duration, Stack,
    aws_iam as iam, 
    aws_lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_ssm as ssm,
)

from constructs import Construct

LAMBDA_TIMEOUT= 900

BASE_LAMBDA_CONFIG = dict (
    timeout=Duration.seconds(LAMBDA_TIMEOUT),       
    architecture=aws_lambda.Architecture.ARM_64,
    tracing= aws_lambda.Tracing.ACTIVE)


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # ======================================================================
        # Lambda Crea el Vector DB
        # ======================================================================


        self.create_vector_db = aws_lambda.DockerImageFunction(
            self, "VectorDB",  
            memory_size=1024,

            code=aws_lambda.DockerImageCode.from_image_asset(
                "./lambdas/code/",
                cmd = [ "build_pdf_vector_db/lambda_function.lambda_handler" ],
                ),
            **BASE_LAMBDA_CONFIG)
        
                # ======================================================================
        # Lambda Crea el Vector DB
        # ======================================================================


        self.create_image_vector_db = aws_lambda.DockerImageFunction(
            self, "ImageVectorDB",  
            memory_size=1024,

            code=aws_lambda.DockerImageCode.from_image_asset(
                "./lambdas/code/",
                cmd = [ "build_image_vector_db/lambda_function.lambda_handler" ],
                ),
            **BASE_LAMBDA_CONFIG)


        # ======================================================================
        # Load Faiss Vector DB (from s3) and retrieves docs
        # ======================================================================
        self.retriever = aws_lambda.DockerImageFunction(
            self, "RetrieverDB",
            memory_size=256,

            code=aws_lambda.DockerImageCode.from_image_asset(
                "./lambdas/code/",
                cmd = [ "pdf_retriever_lambda/lambda_function.lambda_handler" ],
                ),
            **BASE_LAMBDA_CONFIG)
        
         # ======================================================================
        # Load Faiss Vector DB (from s3) and retrieves docs
        # ======================================================================
        self.retriever_image = aws_lambda.DockerImageFunction(
            self, "RetrieverDBImage",
            memory_size=256,

            code=aws_lambda.DockerImageCode.from_image_asset(
                "./lambdas/code/",
                cmd = [ "image_retriever_lambda/lambda_function.lambda_handler" ],
                ),
            **BASE_LAMBDA_CONFIG)
        


        for f in [self.retriever, self.create_vector_db, self.create_image_vector_db, self.retriever_image ]:
            f.add_to_role_policy(iam.PolicyStatement(actions=['s3:*'],resources=["*"]))
            f.add_to_role_policy(iam.PolicyStatement(actions=['bedrock:*'],resources=["*"]))
            f.add_to_role_policy(iam.PolicyStatement( actions=["events:PutEvents"], resources=['*']))

            f.add_permission(
                f'invoke from account',
                principal=iam.AnyPrincipal(),action="lambda:invokeFunction",
                # source_arn=f"arn:aws:lambda:{self.region}:{self.account}:*"
        )