import boto3
import json
from botocore.exceptions import ClientError  # import botocore.exceptions

class PGSetup():
    def __init__(self, client, cluster_arn, secrets_arn, database_name, table_name,credentials_arn):
        self.cluster_arn = cluster_arn
        self.secrets_arn = secrets_arn
        self.credentials_arn = credentials_arn
        self.database_name = database_name
        self.table_name = table_name

        self.client = client

        try:
            response = boto3.client('secretsmanager').get_secret_value(SecretId=credentials_arn)
            creds = json.loads(response.get("SecretString"))
            self.user = creds.get("username")
            self.user_password = creds.get("password")
        except ClientError as e:
            print(f"Error retrieving secret: {e}")
            raise

    def setup(self):
        self.create_extension_vector()
        self.create_schema()
        self.create_role()
        self.grant_privileges()
        self.create_tables()

    def create_tables(self):
        table_name = self.sanitize_table_name(self.table_name)
        sql = f"CREATE TABLE IF NOT EXISTS bedrock_integration.{table_name} (id uuid PRIMARY KEY, embedding vector(1024), chunks text, time integer, metadata json, \"date\" text, source text, sourceurl text, topic text, content_type text, language varchar(10));"

        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.credentials_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        del response['ResponseMetadata']
        logging.info(f"CREATE TABLE  : {response}") # import logging

        response2 = self.client.execute_statement(
            resourceArn=self.cluster_arn, 
            secretArn=self.credentials_arn,
            sql=f"CREATE INDEX on bedrock_integration.{table_name} USING hnsw (embedding vector_cosine_ops)",
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        del response2['ResponseMetadata']
        logging.info(f"CREATE INDEX  : {response2}") # import logging

        return response2

    
    def grant_privileges(self):
        sql = f'GRANT ALL ON SCHEMA bedrock_integration to {self.user}'
        logging.info(f"{sql} :") # import logging
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.secrets_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs='JSON'
        )
        del response['ResponseMetadata']
        logging.info("Privileges granted successfully") # import logging
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
            print(f"CREATE ROLE bedrock_user : Operation completed successfully")
            return response
        except self.client.exceptions.DatabaseErrorException as e:
            print(f"CREATE ROLE bedrock_user : An error occurred")
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
        del response['ResponseMetadata']
        print(f"Schema creation executed successfully")
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
        print(f"SQL executed: {sql}")
        return response
    

