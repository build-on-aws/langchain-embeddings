
from aws_cdk import (
    aws_apigateway as apg,
    Stack,
    aws_lambda as _lambda
)

from constructs import Construct



class WebhookApi(Construct):

    def __init__(self, scope: Construct, construct_id: str,lambda_function:_lambda.Function, cognito=None,  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    

        api = apg.RestApi(self, "videorag")
        api.root.add_cors_preflight(allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

        retriever = api.root.add_resource("retrieve",  default_integration=apg.LambdaIntegration(lambda_function, allow_test_invoke=False))

        base_add_method_kwargs = dict(http_method = "POST")

        if cognito:
            auth = apg.CognitoUserPoolsAuthorizer(self, "apiauthorizer", cognito_user_pools=[cognito])
            print("API with authorizer")
            base_add_method_kwargs = dict(**base_add_method_kwargs, authorizer=auth, authorization_type=apg.AuthorizationType.COGNITO)
        else: 
            print("API without authorizer")


        for res in [ retriever]:
            res.add_method(**base_add_method_kwargs)
            res.add_cors_preflight(allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])
            res.add_method("GET")

        self.retrieve_api_url = api.url_for_path("/retrieve")