import boto3

from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_s3 as s3,
    RemovalPolicy,
    aws_logs as logs,
    aws_iam as iam,
)
from constructs import Construct
from workflows import AudioVideoWorkflow
from lambdas import Lambdas
from databases import Tables

ssm_client = boto3.client("ssm")


class AudioVideoWorkflowStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cluster_arn         = ssm_client.get_parameter(Name="/videopgvector/cluster_arn")["Parameter"]["Value"]
        secret_arn          = ssm_client.get_parameter(Name="/videopgvector/secret_arn")["Parameter"]["Value"]

        video_bucket        = s3.Bucket( self,"VideoBucket", removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True)

        Fn                  = Lambdas(self, "Fn")
        T                   = Tables(self, "T")

        cluster_name        = ssm_client.get_parameter(Name="/cluster-name")["Parameter"]["Value"]
        vpc_id              = ssm_client.get_parameter(Name="/vpc-id")["Parameter"]["Value"]

        Fn.start_transcribe.add_environment( key="BUCKET_NAME", value=video_bucket.bucket_name)
        Fn.start_transcribe.add_environment( key="TRANSCRIBE_TABLE", value=T.transcriptions.table_name)

        Fn.process_transcribe.add_environment( key="BUCKET_NAME", value=video_bucket.bucket_name)
        Fn.process_transcribe.add_environment( key="TRANSCRIBE_TABLE", value=T.transcriptions.table_name)

        Fn.process_results.add_environment(key="CLUSTER_ARN", value=cluster_arn)
        Fn.process_results.add_environment(key="SECRET_ARN", value=secret_arn)

        # Import the existing ECS cluster
        ecs_cluster         = ecs.Cluster.from_cluster_attributes( self, "ImportedCluster", cluster_name=cluster_name, vpc=ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id),security_groups=[],)

        # Create a task execution role
        execution_role = iam.Role( self, "TaskExecutionRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),managed_policies=[ iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")])

        # Create a task role with permissions to access required AWS services
        task_role = iam.Role(self, "TaskRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))

        # Add permissions to the task role as needed
        task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )

        # Create the task definition
        task_definition = ecs.FargateTaskDefinition(
            self,
            "VideoProcessingTaskDef",
            memory_limit_mib=4096,
            cpu=2048,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64,
            ),
            execution_role=execution_role,
            task_role=task_role,
        )

        # Add container to the task definition
        task_definition.add_container(
            "VideoProcessingContainer",
            image=ecs.ContainerImage.from_asset("./container"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="video-processing",
                log_group=logs.LogGroup(
                    self,
                    "VideoProcessingLogGroup",
                    retention=logs.RetentionDays.ONE_WEEK,
                ),
            ),
            environment={"LOG_LEVEL": "INFO"},
        )

        # Create the workflow with the cluster and task definition
        workflow = AudioVideoWorkflow(
            self,
            "wf",
            functions=Fn,
            cluster=ecs_cluster,
            task_definition=task_definition,
        )

        workflow._workflow.grant_task_response(task_role)
        workflow._workflow.grant_task_response(Fn.process_transcribe)

        video_bucket.grant_read_write(task_role)
        video_bucket.grant_read_write(Fn.start_transcribe)
        video_bucket.grant_read_write(Fn.process_transcribe)
        video_bucket.grant_read_write(Fn.process_results)

        T.transcriptions.grant_read_write_data(Fn.process_transcribe)
        T.transcriptions.grant_read_write_data(Fn.start_transcribe)

        task_role.add_to_policy(iam.PolicyStatement(actions=["bedrock:*"], resources=["*"]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["bedrock:*"], resources=["*"]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement"], resources=[cluster_arn]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], resources=[secret_arn]))