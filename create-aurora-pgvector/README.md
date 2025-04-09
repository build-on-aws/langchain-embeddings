# Building an Amazon Aurora PostgreSQL Vector Database

> This documentation was created with the help of [Generating documentation with Amazon Q Developer](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/doc-generation.html)


Learn how to set up an Amazon Aurora PostgreSQL vector database to multimodal vector embeddings, enabling semantic search, using [AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk) for Python.

## The Importance of Vector Databases

Vector databases are essential for implementing Retrieval Augmented Generation (RAG) systems. They provide efficient storage and querying of high-dimensional vector embeddings, enabling semantic search capabilities beyond traditional keyword matching. Amazon Aurora PostgreSQL with vector support and pgvector offers a fully managed database service that's optimized for AI and machine learning workloads.

## Overview of the Setup Process

With [AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk) for Python, you'll:

1. Set up an Amazon Aurora PostgreSQL Serverless v2 database cluster
2. Create a database secret
3. Initialize a custom resource to set up a PostgreSQL table
4. Configure necessary permissions for the custom resource
5. Store key information in [AWS Systems Manager (SSM) Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

> When you complete these steps, you can use your Aurora PostgreSQL database as a [Knowledge Base for Amazon Bedrock](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html).


## 💰 Costs
When you use these AWS services, you incur costs for:

- [Amazon Aurora Pricing](https://aws.amazon.com/rds/aurora/pricing/)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [AWS Systems Manager Pricing](https://aws.amazon.com/systems-manager/pricing/)

##  Setup Overview

he setup uses an AWS Lambda function through a custom resource in CDK, with these key components:

![Architecture diagram - Part 1](images/part_1.jpg)

The preparation includes:

1. Install the pgvector extension (version 0.5.0 or higher):
```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extversion FROM pg_extension WHERE extname='vector';
```
This enables vector storage and HNSW indexing, crucial for efficient similarity searches.

2. Create a dedicated schema and user role:
```sql
CREATE SCHEMA bedrock_integration;
CREATE ROLE bedrock_user WITH PASSWORD 'your_secure_password' LOGIN;
```
This segregates our Bedrock-related data and provides controlled access.

3. Grant permissions to the bedrock_user:
```sql
GRANT ALL ON SCHEMA bedrock_integration to bedrock_user;
```
This allows the user to manage the schema, including creating tables and indexes.

4. Create the knowledge base table:
```sql
CREATE TABLE IF NOT EXISTS bedrock_integration.bedrock_kb (
    id uuid PRIMARY KEY,
    embedding vector(1024),
    chunks text,
    metadata json,
    topic text,
    language varchar(10)
);
```
This table structure includes:
- `id`: Unique identifier for each document chunk
- `embedding`: Vector representation of the text (1024 dimensions for Amazon Titan/Cohere)
- `chunks`: The actual text content
- `metadata`: Flexible JSON field for document properties
- `topic` and `language`: Optional fields for document filtering

For more details about metadata filtering, see the [Knowledge Base documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-ds.html#kb-ds-metadata).

5. Create an index for efficient similarity searches:
```sql
CREATE INDEX ON bedrock_integration.bedrock_kb USING hnsw (embedding vector_cosine_ops);
```
This HNSW (Hierarchical Navigable Small World) index optimizes cosine similarity searches.

## Building the Infrastructure

✅ To set up this infrastructure:

1. Navigate to the project directory:
```bash
cd 01-create-aurora-pgvector
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
For Windows:
```batch
.venv\Scripts\activate.bat
```

> For more information, see the [CDK Guide](https://docs.aws.amazon.com/cdk/v2/guide/hello_world.html)

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Deploy the CDK stack (this may take some time):
```bash
cdk deploy
```

You can monitor the deployment progress in the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation).

### About the VPC

This stack creates a new VPC. Be aware of [VPC service limits](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html) in your AWS account. The VPC is created with:

```python
# Create a VPC
self.vpc = ec2.Vpc(self, "VPC", 
    max_azs=2,  # Use 2 Availability Zones
    nat_gateways=0  # Save costs by not using NAT gateways
)
```

You can modify the CDK code to use an existing VPC if preferred.

### Verify the Aurora Serverless Cluster

1. Go to the [RDS Query Editor](https://console.aws.amazon.com/rds/home#query-editor:)
2. Access your cluster using the Database Secret ARN (`bedrockSecret-xxx`)
3. Execute the following query to verify the table creation:
```sql
SELECT * FROM bedrock_integration.bedrock_kb LIMIT 5;
```

![RDS Query Editor](images/check_aurora.png)

### Security Best Practices

Database credentials are stored securely in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), following AWS security best practices.


> 👾 Note: You can customize the Aurora PostgreSQL Serverless v2 database cluster [settings](https://github.com/aws-samples/aws-cdk-examples/tree/master/python/rds/aurora-serverless-v2) according to your needs.

