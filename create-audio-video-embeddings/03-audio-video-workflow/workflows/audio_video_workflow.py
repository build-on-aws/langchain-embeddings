from aws_cdk import (
    aws_stepfunctions as sf,
    aws_logs,
    aws_stepfunctions_tasks as sft,
    aws_ecs as ecs,
    Duration,
)

from .lambda_steps_helper import start_transcribe_task, process_results_task
from constructs import Construct


retry_options = dict(
    backoff_rate=2,
    interval=Duration.seconds(10),
    max_attempts=10,
    errors=[
        "Lambda.ServiceException",
        "Lambda.AWSLambdaException",
        "Lambda.SdkClientException",
        "Lambda.TooManyRequestsException",
        "States.TaskFailed",
        "ECS.TaskFailedReason",
    ],
)
from lambdas import Lambdas


class AudioVideoWorkflow(Construct):
    @property
    def workflow(self) -> sf.StateMachine:
        return self._workflow

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        functions: Lambdas,
        cluster: ecs.ICluster,
        task_definition: ecs.TaskDefinition,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        start_transcribe_step = start_transcribe_task(self, functions)
        process_results_step = process_results_task(self, functions)

        # Create the ECS Run Task that will process the video
        run_ecs_task = sft.EcsRunTask(
            self,
            "ProcessVideoTask",
            integration_pattern=sf.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
            cluster=cluster,
            task_definition=task_definition,
            assign_public_ip=False,  # Required for Fargate tasks in public subnets
            launch_target=sft.EcsFargateLaunchTarget(
                platform_version=ecs.FargatePlatformVersion.LATEST
            ),
            container_overrides=[
                sft.ContainerOverride(
                    container_definition=task_definition.default_container,
                    environment=[
                        sft.TaskEnvironmentVariable(
                            name="S3_URI", value=sf.JsonPath.string_at("$.s3_uri")
                        ),
                        sft.TaskEnvironmentVariable(
                            name="TASK_TOKEN", value=sf.JsonPath.task_token
                        ),
                    ],
                )
            ],
        )

        # Add retry options to both tasks
        run_ecs_task_with_retry = run_ecs_task.add_retry(**retry_options)

        # Create a parallel state to run both tasks simultaneously
        parallel_tasks = sf.Parallel(self,"Audio Video Processor",
            result_selector={
                "video_workflow.$": "$[0]",
                "audio_workflow.$": "$[1]",
            },
            result_path="$.audio_video_processor",
        )

        # Add both tasks to the parallel state
        parallel_tasks.branch(run_ecs_task_with_retry)
        parallel_tasks.branch(start_transcribe_step)

        parallel_tasks.next(process_results_step)

        # Define the workflow
        definition = parallel_tasks

        # Create the state machine
        self._workflow = sf.StateMachine(
            self,
            "VideoProcessingWorkflow",
            definition_body=sf.DefinitionBody.from_chainable(definition),
            timeout=Duration.hours(4),
            logs=sf.LogOptions(
                destination=aws_logs.LogGroup(self, "VideoWorkflowLogs"),
                level=sf.LogLevel.ALL,
            ),
        )
