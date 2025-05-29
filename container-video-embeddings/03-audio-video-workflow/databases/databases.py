from aws_cdk import (
    RemovalPolicy,
    aws_dynamodb as ddb
)
from constructs import Construct


REMOVAL_POLICY = RemovalPolicy.RETAIN

TABLE_CONFIG = dict (removal_policy=REMOVAL_POLICY, billing_mode= ddb.BillingMode.PAY_PER_REQUEST)




class Tables(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    
        self.transcriptions = ddb.Table(
            self, "Transcriptions",
            partition_key=ddb.Attribute(name="TranscriptionJobName", type=ddb.AttributeType.STRING),
            **TABLE_CONFIG)

