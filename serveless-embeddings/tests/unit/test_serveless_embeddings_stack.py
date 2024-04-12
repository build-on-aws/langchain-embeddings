import aws_cdk as core
import aws_cdk.assertions as assertions

from serveless_embeddings.serveless_embeddings_stack import ServelessEmbeddingsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in serveless_embeddings/serveless_embeddings_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ServelessEmbeddingsStack(app, "serveless-embeddings")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
