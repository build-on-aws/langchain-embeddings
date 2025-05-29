import aws_cdk as core
import aws_cdk.assertions as assertions

from 04_retrieval.04_retrieval_stack import 04RetrievalStack

# example tests. To run these tests, uncomment this file along with the example
# resource in 04_retrieval/04_retrieval_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = 04RetrievalStack(app, "04-retrieval")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
