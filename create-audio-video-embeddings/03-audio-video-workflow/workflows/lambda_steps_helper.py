from aws_cdk import (
    aws_stepfunctions as sf,
    aws_stepfunctions_tasks as sft,
    Duration,
)

retry_options = dict(
    backoff_rate=2,
    interval=Duration.seconds(10),
    max_attempts=6,
    errors=[
        "Lambda.ServiceException",
        "Lambda.AWSLambdaException",
        "Lambda.SdkClientException",
        "Lambda.TooManyRequestsException",
        "States.TaskFailed",
    ],
)
from lambdas import Lambdas



def start_transcribe_task(self, Fn: Lambdas):
    task = sft.LambdaInvoke(
        self,
        "Start Transcribe Wait",
        lambda_function=Fn.start_transcribe,
        result_path="$",
        payload=sf.TaskInput.from_object(
            {
                "s3_uri": sf.JsonPath.string_at("$.s3_uri"),
                "sftoken": sf.JsonPath.task_token,
            }
        ),
        task_timeout=sf.Timeout.duration(Duration.seconds(1800)),
        integration_pattern=sf.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
    )
    task.add_retry(**retry_options)
    return task


def process_results_task(self, Fn: Lambdas):
    task= sft.LambdaInvoke(
        self,
        "ProcessResults",
        payload_response_only=True,
        lambda_function=Fn.process_results,
        result_path="$",
    )
    task.add_retry(**retry_options)
    return task