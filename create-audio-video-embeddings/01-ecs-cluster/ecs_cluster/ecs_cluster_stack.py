from aws_cdk import (
    aws_ssm as ssm,
    aws_ecs as ecs,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct


class EcsClusterStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ecs_cluster = ecs.Cluster(self, "Cluster", cluster_name="video-processing")

        ssm.StringParameter(
            self,
            "ssm-cluster",
            parameter_name="/cluster-name",
            string_value=ecs_cluster.cluster_name,
        )
        
        # Save the VPC ID in SSM Parameter Store
        ssm.StringParameter(
            self,
            "ssm-vpc-id",
            parameter_name="/vpc-id",
            string_value=ecs_cluster.vpc.vpc_id,
        )
