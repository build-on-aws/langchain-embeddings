
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    RemovalPolicy,
)
from constructs import Construct


class AuroraDatabaseCluster(Construct):
    def __init__(self, scope: Construct, construct_id: str, default_database_name,acu = 0.5, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Crear una VPC
        self.vpc = ec2.Vpc(self, "VPC", max_azs=2, nat_gateways=0)

        # Crear un grupo de seguridad para la base de datos
        self.security_group = ec2.SecurityGroup(
            self, "SecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True
        )

        # Crear un cluster de base de datos Aurora PostgreSQL Serveless V2
        self.cluster = rds.DatabaseCluster(
            self, "AuroraPostgreSQLCluster",
            default_database_name= default_database_name,
            engine=rds.DatabaseClusterEngine.aurora_postgres(version=rds.AuroraPostgresEngineVersion.VER_16_2),
            credentials=rds.Credentials.from_generated_secret("clusteradmin"),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            serverless_v2_min_capacity=acu,
            serverless_v2_max_capacity=acu*2,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            vpc=self.vpc,
            removal_policy=RemovalPolicy.DESTROY, 
            enable_data_api=True #In order for use the endpoint to run SQL statements without managing connections.

        )

        # Agregar el grupo de seguridad al cluster de base de datos
        self.cluster.connections.allow_default_port_from(self.security_group)
