from aws_cdk import (
    aws_iam as iam, Stack,
    aws_cognito as cognito,RemovalPolicy,
    CfnOutput
)

from constructs import Construct



class UserPool(Construct):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


        stk = Stack.of(self)
        region = stk.region

        self.user_pool = cognito.UserPool(
            self, "user_pool",
            password_policy = cognito.PasswordPolicy(min_length=8),
            self_sign_up_enabled = False, 
            standard_attributes = cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True),
                #fullname=cognito.StandardAttribute(required=True)
                ),
            sign_in_aliases= cognito.SignInAliases(email=True),
            removal_policy= RemovalPolicy.DESTROY,
            account_recovery= cognito.AccountRecovery.EMAIL_ONLY,
            auto_verify = cognito.AutoVerifiedAttrs(email=True)
        )


        self.user_pool_client = cognito.UserPoolClient(self, "Client",
            user_pool=self.user_pool,
            generate_secret=False)
        
        
        self.pool_id = self.user_pool.user_pool_id
        self.app_client_id = self.user_pool_client.user_pool_client_id
        #self.app_client_secret = self.user_pool_client.user_pool_client_secret.unsafe_unwrap()
        cognito_console_url = f"https://{region}.console.aws.amazon.com/cognito/v2/idp/user-pools/{self.pool_id}/users?region={region}"


        CfnOutput(self, 'POOL_ID',value=self.pool_id)
        
        CfnOutput(self, 'APP_CLIENT_ID',value=self.app_client_id)

        #CfnOutput(self, 'APP_CLIENT_SECRET',value=self.app_client_secret)

        CfnOutput(self, 'cognito_console', description="Crear usuario acá",  value=cognito_console_url)