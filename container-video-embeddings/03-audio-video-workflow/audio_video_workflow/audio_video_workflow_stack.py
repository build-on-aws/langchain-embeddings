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
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3_notifications,
    aws_s3_deployment as s3deploy # Add this import
)
from constructs import Construct
from workflows import AudioVideoWorkflow
from lambdas import Lambdas
from databases import Tables


class AudioVideoWorkflowStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create SSM client with the same region as the stack
        ssm_client = boto3.client("ssm", region_name=self.region)

        cluster_arn         = ssm_client.get_parameter(Name="/videopgvector/cluster_arn")["Parameter"]["Value"]
        secret_arn          = ssm_client.get_parameter(Name="/videopgvector/secret_arn")["Parameter"]["Value"]

        video_bucket        = s3.Bucket( self,"VideoBucket", removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True)

        Fn                  = Lambdas(self, "Fn")
        T                   = Tables(self, "T")

        cluster_name        = ssm_client.get_parameter(Name="/videopgvector/ecs-cluster-name")["Parameter"]["Value"]
        vpc_id              = ssm_client.get_parameter(Name="/videopgvector/ecs-vpc-id")["Parameter"]["Value"]

        Fn.start_transcribe.add_environment( key="BUCKET_NAME", value=video_bucket.bucket_name)
        Fn.start_transcribe.add_environment( key="TRANSCRIBE_TABLE", value=T.transcriptions.table_name)

        ssm.StringParameter( self, "bucket_name", parameter_name=f"/videopgvector/bucket_name", string_value=video_bucket.bucket_name)


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

        workflow._workflow.from_state_machine_arn

        video_bucket.grant_read_write(task_role)
        video_bucket.grant_read_write(Fn.start_transcribe)
        video_bucket.grant_read_write(Fn.process_transcribe)
        video_bucket.grant_read_write(Fn.process_results)
        video_bucket.grant_read_write(Fn.s3_trigger)

        T.transcriptions.grant_read_write_data(Fn.process_transcribe)
        T.transcriptions.grant_read_write_data(Fn.start_transcribe)

        task_role.add_to_policy(iam.PolicyStatement(actions=["bedrock:*"], resources=["*"]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["bedrock:*"], resources=["*"]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["rds-data:ExecuteStatement"], resources=[cluster_arn]))
        Fn.process_results.add_to_role_policy(iam.PolicyStatement(actions=["secretsmanager:GetSecretValue"], resources=[secret_arn]))

        Fn.s3_trigger.add_environment("STATE_MACHINE_ARN", workflow._workflow.state_machine_arn)
        Fn.s3_trigger.add_environment("BUCKET_NAME", video_bucket.bucket_name)
        ssm.StringParameter( self, "S_M_ARN", parameter_name=f"/videopgvector/state_machine_arn", string_value=workflow._workflow.state_machine_arn)


        video_bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                              aws_s3_notifications.LambdaDestination(Fn.s3_trigger),
                                              s3.NotificationKeyFilter(prefix="video/"))
        
        # Create empty folders (prefixes) in the bucket
        s3deploy.BucketDeployment(self, "CreateFolders",
        sources=[s3deploy.Source.data("video/placeholder.txt", "")], # Creates voice_ folder
        destination_bucket=video_bucket,
        retain_on_delete=False,
        )
    
        Fn.s3_trigger.add_to_role_policy(
            iam.PolicyStatement(
                actions=["states:StartExecution"],
                resources=[workflow._workflow.state_machine_arn],
            )
        )