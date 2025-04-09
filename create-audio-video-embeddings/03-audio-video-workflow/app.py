#!/usr/bin/env python3
import os
import boto3
import aws_cdk as cdk

region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
caller = boto3.client('sts').get_caller_identity()
account_id = caller.get("Account")


from audio_video_workflow.audio_video_workflow_stack import AudioVideoWorkflowStack


app = cdk.App()
AudioVideoWorkflowStack(app, "WORKFLOW-STACK", env=cdk.Environment(account=account_id, region=region))

app.synth()
