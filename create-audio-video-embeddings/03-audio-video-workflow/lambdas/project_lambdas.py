from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    Size,
    aws_events as events,
    aws_events_targets as targets,
)

from constructs import Construct

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(900),
    memory_size=256,
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)


class Lambdas(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # ======================================================================
        # Lambda Comienza el proceso de transcribe
        # ======================================================================

        self.start_transcribe = aws_lambda.Function(
            self,
            "StartTranscribe",
            code=aws_lambda.Code.from_asset("./lambdas/code/start_transcribe/"),
            handler="lambda_function.lambda_handler",
            **BASE_LAMBDA_CONFIG,
        )

        self.start_transcribe.add_to_role_policy(
            iam.PolicyStatement(
                actions=["transcribe:StartTranscriptionJob"], resources=["*"]
            )
        )

        # ======================================================================
        # Lambda  procesa la transcripcion
        # ======================================================================
        self.process_transcribe = aws_lambda.Function(
            self,
            "ProcessTranscription",
            code=aws_lambda.Code.from_asset("./lambdas/code/process_transcribe/"),
            handler="lambda_function.lambda_handler",
            **BASE_LAMBDA_CONFIG,
        )
        self.process_transcribe.add_to_role_policy(
            iam.PolicyStatement(
                actions=["transcribe:GetTranscriptionJob"], resources=["*"]
            )
        )

        # ======================================================================
        # Lambda  procesa la transcripcion y los frames
        # ======================================================================
        self.process_results = aws_lambda.Function(
            self,
            "ProcessResults",
            code=aws_lambda.Code.from_asset("./lambdas/code/process_results/"),
            handler="lambda_function.lambda_handler",
            **BASE_LAMBDA_CONFIG,
        )


        event_rule = events.Rule(
            self,
            "transcriptionJobEnd",
            description="Transcription Job End",
            event_pattern=events.EventPattern(
                source=["aws.transcribe"],
                detail_type=["Transcribe Job State Change"],
                detail={"TranscriptionJobStatus": ["COMPLETED", "FAILED"]},
            ),
        )
        event_rule.add_target(targets.LambdaFunction(handler=self.process_transcribe))
