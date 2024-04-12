import json
from aws_cdk import (
    Stack,
    aws_ssm as ssm,
)
from constructs import Construct
from lambdas import Lambdas

class ServelessEmbeddingsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        Fn  = Lambdas(self,'Fn')

        CREATE_VECTOR_DB_ARN = Fn.create_vector_db.function_arn
        CREATE_IMAGE_VECTOR_DB_ARN = Fn.create_image_vector_db.function_arn
        RETRIEVE_VECTOR_DB_ARN = Fn.retriever.function_arn
        RETRIEVE_IMAGE_VECTOR_DB_ARN = Fn.retriever_image.function_arn
       

        parameter = {
            "CREATE_VECTOR_DB_ARN": CREATE_VECTOR_DB_ARN,
            "RETRIEVE_VECTOR_DB_ARN": RETRIEVE_VECTOR_DB_ARN,
            "CREATE_IMAGE_VECTOR_DB_ARN": CREATE_IMAGE_VECTOR_DB_ARN,
            "RETRIEVE_IMAGE_VECTOR_DB_ARN": RETRIEVE_IMAGE_VECTOR_DB_ARN,
        }

        ssm.StringParameter(self, "api", parameter_name="vector_lambdas", string_value=json.dumps(parameter))   

