import boto3
from aws_cdk import (
    aws_ssm as ssm,
    aws_ec2 as ec2,
    Stack,
    aws_lambda,
    aws_iam as iam,
    aws_rds as rds,
    CustomResource
)
from constructs import Construct
from aurora_postgres import AuroraDatabaseCluster
from layers import RequestsAWSAuth
from lambdas import Lambdas


ssm_client              = boto3.client("ssm")
bedrock_user            = "bedrock_user"
table_name              = "knowledge_bases"
default_database_name   = "kbdata"


class AuroraPgVectorVideoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_id = ssm_client.get_parameter(Name="/vpc-id")["Parameter"]["Value"]
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)

        self.cluster = AuroraDatabaseCluster(self, "AuroraDB", vpc=vpc, default_database_name=default_database_name)

        self.bedrock_secret = rds.DatabaseSecret(
            self,
            "bedrockSecret",
            username=bedrock_user,
            exclude_characters=" ,%+~`#$&*()|[]{}:;<>?!'/@\".=",
        )

        Fn = Lambdas(self, "Fn")
        
        
        pg_setup = CustomResource( self,
            "pg_setup",
            resource_type="Custom::PGSetup",
            service_token= Fn.table_creator.function_arn,
            properties=dict(
                cluster_arn=self.cluster.cluster.cluster_arn,
                secrets_arn= self.cluster.cluster.secret.secret_arn,
                table_name=table_name,
                database_name=default_database_name,
                credentials_arn = self.bedrock_secret.secret_arn,
            )
        ) 
        pg_setup.node.add_dependency(self.cluster.cluster)
        pg_setup.node.add_dependency(self.bedrock_secret) 

        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement"], 
                                                                resources=[self.cluster.cluster.cluster_arn]))
        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], 
                                                                resources=[self.cluster.cluster.secret.secret_arn]))
        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], 
                                                                resources=[self.bedrock_secret.secret_arn]))

        ssm.StringParameter( self, "cluster_arn_ssm", parameter_name=f"/videopgvector/cluster_arn", string_value=self.cluster.cluster.cluster_arn)
        ssm.StringParameter( self, "secret_arn_ssm", parameter_name=f"/videopgvector/secret_arn", string_value=self.bedrock_secret.secret_arn)
        ssm.StringParameter( self, "table_ssm", parameter_name=f"/videopgvector/video_table_name", string_value=table_name) 