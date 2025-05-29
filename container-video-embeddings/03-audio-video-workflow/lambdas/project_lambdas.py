from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
    Size,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3 as s3,
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
        # Lambda que se activa cuando se carga un video en S3
        # ======================================================================
        self.s3_trigger = aws_lambda.Function(
            self,
            "S3Trigger",
            code=aws_lambda.Code.from_asset("./lambdas/code/s3_trigger/"),
            handler="lambda_function.lambda_handler",
            **BASE_LAMBDA_CONFIG,
        )

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

    def configure_s3_trigger(self, bucket, state_machine):
        """
        Configura la lambda de S3 trigger con los permisos y variables de entorno necesarios.
        Esta función debe ser llamada después de que el bucket y la máquina de estados existan.
        
        Args:
            bucket: El bucket de S3 que activará la lambda
            state_machine: La máquina de estados que será iniciada por la lambda
        """
        if not bucket or not state_machine:
            raise ValueError("El bucket y la máquina de estados deben existir para configurar el trigger de S3")
        
        # Configurar variables de entorno
        self.s3_trigger.add_environment("STATE_MACHINE_ARN", state_machine.state_machine_arn)
        self.s3_trigger.add_environment("BUCKET_NAME", bucket.bucket_name)
        
        # Agregar permisos para iniciar la máquina de estados
        self.s3_trigger.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[state_machine.state_machine_arn],
            )
        )
        
        # Configurar el evento de S3 para activar la lambda
        self.s3_trigger.add_event_source(
            lambda_event_sources.S3EventSource(
                bucket,
                events=[s3.EventType.OBJECT_CREATED],
                filters=[
                    s3.NotificationKeyFilter(suffix=".mp4"),
                    s3.NotificationKeyFilter(suffix=".mov"),
                    s3.NotificationKeyFilter(suffix=".avi"),
                    s3.NotificationKeyFilter(suffix=".mkv"),
                    s3.NotificationKeyFilter(suffix=".wmv"),
                ],
            )
        )