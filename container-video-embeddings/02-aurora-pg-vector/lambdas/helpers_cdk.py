from aws_cdk import aws_iam as iam, Duration, Size, aws_lambda
def add_permisions (self ):

    for f in [
    self.start_transcribe,
    self.start_processing,
    self.process_transcribe,

    self.ffmpeg_process,
    self.ffmpeg_split_video,
    self.combine_frames,
    
    self.start_summarization,
    self.summary,
    self.consolidate_summary,
    self.generate_presign_url,

    self.create_vector_db,
    self.retriever

    ]:
        f.add_to_role_policy(iam.PolicyStatement(actions=["s3:*"], resources=["*"]))
        f.add_to_role_policy(iam.PolicyStatement(actions=["dynamodb:*"], resources=["*"]))
        f.add_to_role_policy(iam.PolicyStatement(actions=["bedrock:*"], resources=["*"]))
        f.add_to_role_policy(iam.PolicyStatement(actions=["ssm:GetParameter*"], resources=["*"]))
        f.add_to_role_policy( iam.PolicyStatement(actions=["transcribe:*"], resources=["*"]))



LAMBDA_TIMEOUT = 900

DOCKER_LAMBDA_CONF = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)
BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    memory_size=256,
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
)