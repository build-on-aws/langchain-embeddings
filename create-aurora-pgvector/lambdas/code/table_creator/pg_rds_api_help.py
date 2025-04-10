
import boto3
import json
class PGSetup():
    def __init__(self, client, cluster_arn, secrets_arn, database_name, table_name,credentials_arn):
        self.cluster_arn = cluster_arn
        self.secrets_arn = secrets_arn
        self.credentials_arn = credentials_arn
        self.database_name = database_name
        self.table_name = table_name

        self.client = client

        response =  boto3.client('secretsmanager').get_secret_value(SecretId=credentials_arn)
        creds = json.loads(response.get("SecretString"))
        self.user = creds.get("username")
        self.user_password = creds.get("password")

    def setup(self):
        self.create_extension_vector()
        self.create_schema()
        self.create_role()
        self.grant_privileges()
        self.create_tables()

    def create_tables(self):
        table_name = self.sanitize_table_name(self.table_name)
        sql = f"CREATE TABLE IF NOT EXISTS bedrock_integration.{table_name} (id uuid PRIMARY KEY, embedding vector(1024), chunks text, metadata json, \"date\" text, source text, topic text, language varchar(10));"

        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.credentials_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        if response.get('ResponseMetadata') is not None:
            del response['ResponseMetadata']
        else:
            raise TypeError("Response metadata could not be retrieved due to NoneType response.")
        print(f"CREATE TABLE  : {response}")


        response2 = self.client.execute_statement(
            resourceArn=self.cluster_arn, 
            secretArn=self.credentials_arn,
            sql=f"CREATE INDEX on bedrock_integration.{table_name} USING hnsw (embedding vector_cosine_ops)",
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        if response2.get('ResponseMetadata') is not None:
            del response2['ResponseMetadata']
        else:
            raise TypeError("Response metadata could not be retrieved due to NoneType response.")
        print(f"CREATE INDEX  : {response2}")

        return response2
    
    def create_table_multimodal(self):
        table_name = self.sanitize_table_name(self.table_name)
        sql = f"CREATE TABLE IF NOT EXISTS bedrock_integration.{table_name} (id uuid PRIMARY KEY, embedding vector(1024), text TEXT, chunks text, metadata json, \"date\" text, source text, topic text, language varchar(10));"

        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.credentials_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        del response['ResponseMetadata']
        print(f"CREATE TABLE  : {response}")

        return response


    
    def grant_privileges(self):
        sql = f'GRANT ALL ON SCHEMA bedrock_integration to {self.user}'
        print(f"{sql} :", end="")
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.secrets_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        if response.get('ResponseMetadata') is not None:
            del response['ResponseMetadata']
        else:
            print("Response metadata not found")
        print (response)
        return response


    def create_role(self):
        try:
            response = self.client.execute_statement(
                resourceArn=self.cluster_arn, 
                secretArn=self.secrets_arn,
                sql=f"CREATE ROLE {self.user} LOGIN PASSWORD '{self.user_password}'",
                database=self.database_name,
                formatRecordsAs='JSON'
            )
            del response['ResponseMetadata']
            print("CREATE ROLE bedrock_user : Success")
            return response
        except self.client.exceptions.DatabaseErrorException as e:
            print("CREATE ROLE bedrock_user : Error occurred")
            return e

    def create_schema(self):
        sql = 'CREATE SCHEMA IF NOT EXISTS bedrock_integration'
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn, 
            secretArn=self.secrets_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        if response.get('ResponseMetadata') is not None:
            del response['ResponseMetadata']
        else:
            raise TypeError("Response metadata could not be retrieved due to NoneType response.")
        print(f"{sql} : {response}")
        return response

    def create_extension_vector(self):
        sql = 'CREATE EXTENSION IF NOT EXISTS vector'
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn, 
            secretArn=self.secrets_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        del response['ResponseMetadata']
        print(f"{sql} : {response}")
        return response
    
