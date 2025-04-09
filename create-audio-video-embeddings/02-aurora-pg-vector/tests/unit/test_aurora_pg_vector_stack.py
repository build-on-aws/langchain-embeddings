import aws_cdk as core
import aws_cdk.assertions as assertions

from aurora_pg_vector.aurora_pg_vector_stack import AuroraPgVectorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aurora_pg_vector/aurora_pg_vector_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AuroraPgVectorStack(app, "aurora-pg-vector")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
