from aws_cdk import (
    Stack,
    CustomResource,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_rds as rds
)
import json

from constructs import Construct
from rds import AuroraDatabaseCluster
from lambdas import Lambdas

class CreateAuroraPgvectorStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        default_database_name = "kbdata"
        bedrock_user = "bedrock_user"
        table_name = 'knowledge_bases'

        aur = AuroraDatabaseCluster(self, "AuroraDatabaseCluster", default_database_name)

        bedrock_secret = rds.DatabaseSecret(self, "bedrockSecret", username=bedrock_user, exclude_characters=" ,%+~`#$&*()|[]{}:;<>?!'/@\".=")
        Fn = Lambdas(self, "L")
        
         
        pg_setup = CustomResource( self,
            "pg_setup",
            resource_type="Custom::PGSetup",
            service_token=Fn.table_creator.function_arn,
            properties=dict(
                cluster_arn=aur.cluster.cluster_arn,
                secrets_arn= aur.cluster.secret.secret_arn,
                table_name=table_name,
                database_name=default_database_name,
                credentials_arn = bedrock_secret.secret_arn,
            )
        ) 
        pg_setup.node.add_dependency(aur.cluster)
        pg_setup.node.add_dependency(bedrock_secret) 
        
        
        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement"], 
                                                                resources=[aur.cluster.cluster_arn]))
        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], 
                                                                resources=[aur.cluster.secret.secret_arn]))
        Fn.table_creator.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], 
                                                                resources=[bedrock_secret.secret_arn]))

        ssm.StringParameter( self, "cluster_arn_ssm", parameter_name=f"/pgvector/cluster_arn", string_value=aur.cluster.cluster_arn)
        ssm.StringParameter( self, "secret_arn_ssm", parameter_name=f"/pgvector/secret_arn", string_value=bedrock_secret.secret_arn)
        ssm.StringParameter( self, "table_ssm", parameter_name=f"/pgvector/table_name", string_value=table_name) 
