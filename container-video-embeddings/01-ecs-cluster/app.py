#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk

from ecs_cluster import EcsClusterStack

region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2") # "us-east-1")
caller = boto3.client('sts').get_caller_identity()
account_id = caller.get("Account")

app = cdk.App()

EcsClusterStack(app, "VPC-ECS-CLUSTER-STACK")

app.synth()
