import json
from constructs import Construct

from aws_cdk import (
    aws_lambda as _lambda
)



class LangchainCore(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        langchain_core = _lambda.LayerVersion(
            self,
            "Langchain-Core",
            code=_lambda.Code.from_asset("./layers/langchain-core.zip"),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_10,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_12,
                _lambda.Runtime.PYTHON_3_13,
            ],
            description="Langchain Core",
        )
        self.layer = langchain_core
