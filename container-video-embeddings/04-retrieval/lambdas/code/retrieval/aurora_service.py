
import boto3
from typing import List
ssm = boto3.client("ssm")


class AuroraPostgres:
    def __init__(self, cluster_arn, database_name, credentials_arn):
        self.cluster_arn = cluster_arn
        self.credentials_arn = credentials_arn
        self.database_name = database_name
        self.client = boto3.client("rds-data")

    def execute_statement(self, sql):
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.credentials_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs="JSON",
        )
        del response["ResponseMetadata"]
        return response

    def insert(self, rows):
        for row in rows:
            sql = f"\
                INSERT INTO bedrock_integration.knowledge_bases (id, embedding, chunks, time, metadata, date, source, sourceurl, topic, content_type, language) \
                VALUES ('{row['id']}', '{row['embedding']}', '{row['chunks']}','{row['time']}','{row['metadata']}', '{row['date']}', \
                    '{row['source']}','{row['sourceurl']}','{row['topic']}','{row['content_type']}', '{row['language']}')"
            self.execute_statement(sql)

    def similarity_search(self, vector, how="cosine", k=5, filter:List=[None]):


        if how == "l2":
            method = "<->"
            sql = f"SELECT *, embedding {method} '{vector}' AS distance FROM bedrock_integration.knowledge_bases ORDER BY distance LIMIT {k}"

        if how == "cosine":
            method = "<=>"
            sql = f"SELECT *, 1- (embedding {method} '{vector}') AS similarity FROM bedrock_integration.knowledge_bases ORDER BY similarity desc LIMIT {k}"
            
        if len(filter):
            where = f" WHERE {filter[0]['key']} = '{filter[0]['value']}'"
            for f in filter[1:]:
                where += f" AND {f['key']} = '{f['value']}'"
            sql = sql.replace("ORDER BY", f"{where} ORDER BY")
        #print (f"SQL:{sql}")
        response = self.execute_statement(sql)
        return response


def get_ssm_parameter(name):
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]