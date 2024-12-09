import aws_cdk as core
import aws_cdk.assertions as assertions

from create_aurora_pgvector.create_aurora_pgvector_stack import CreateAuroraPgvectorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in create_aurora_pgvector/create_aurora_pgvector_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CreateAuroraPgvectorStack(app, "create-aurora-pgvector")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
