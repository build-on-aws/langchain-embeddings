#!/usr/bin/env python3

import os
import boto3
import aws_cdk as cdk

from aurora_pg_vector import AuroraPgVectorVideoStack

region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
caller = boto3.client('sts').get_caller_identity()
account_id = caller.get("Account")

app = cdk.App()

AuroraPgVectorVideoStack(app, "AURORA-PGVEC-STACK", env=cdk.Environment(account=account_id, region=region))

app.synth()
