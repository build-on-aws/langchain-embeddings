
import boto3

"""
This code defines a AuroraPostgres 
class that interacts with Amazon Aurora PostgreSQL 
using the AWS RDS Data API.

"""

class AuroraPostgres:
    def __init__(self, cluster_arn, database_name, credentials_arn,region_name):
        self.cluster_arn = cluster_arn
        self.credentials_arn = credentials_arn
        self.database_name = database_name
        self.client = boto3.client(service_name="rds-data", region_name=region_name)

    def execute_statement(self, sql):
        #print(sql, end=" ")
        response = self.client.execute_statement(
            resourceArn=self.cluster_arn,
            secretArn=self.credentials_arn,
            sql=sql,
            database=self.database_name,
            formatRecordsAs="JSON",
        )
        del response["ResponseMetadata"]
        #print(f"RESULT  : {response}")
        return response

    def insert(self, rows):
        for row in rows:
            sql = f"\
                INSERT INTO bedrock_integration.knowledge_bases (id, embedding, chunks, time, metadata, date, source, sourceurl, topic, content_type, language) \
                VALUES ('{row['id']}', '{row['embedding']}', '{row['chunks']}','{row['time']}','{row['metadata']}', '{row['date']}', \
                    '{row['source']}','{row['sourceurl']}','{row['topic']}','{row['content_type']}', '{row['language']}')"
            self.execute_statement(sql)

    # Look here https://github.com/pgvector/pgvector
    def similarity_search(self, vector, how="cosine", k=5):
        
        if how == "l2":
            method = "<->"
            sql = f"SELECT *, embedding {method} '{vector}' AS distance  FROM bedrock_integration.knowledge_bases ORDER BY distance LIMIT {k}"

        if how == "cosine":
            method = "<=>"
            sql = f"SELECT *, 1- (embedding {method} '{vector}') AS similarity  FROM bedrock_integration.knowledge_bases ORDER BY similarity desc LIMIT {k}"
            
        response = self.execute_statement(sql)
        return response
