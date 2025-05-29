#!/usr/bin/env python3
import os
import boto3

import aws_cdk as cdk

region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2") # "us-east-1")
caller = boto3.client('sts').get_caller_identity()
account_id = caller.get("Account")

from retrieval.retrieval_stack import RetrievalStack


app = cdk.App()
RetrievalStack(app, "RetrievalStack", env=cdk.Environment(account=account_id, region=region))

app.synth()
