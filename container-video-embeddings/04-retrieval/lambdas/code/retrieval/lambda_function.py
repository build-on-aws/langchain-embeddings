import json
import os
from multimodal_retriever import CustomMultimodalRetriever
from aurora_service import AuroraPostgres
from utils import build_response
from parse_retrieved_docs import parse_docs_for_context, text_content_block
from bedrock_llm import ThinkingLLM

# Get Data from environment variables, never share secrets!
cluster_arn = os.environ.get("CLUSTER_ARN")
credentials_arn = os.environ.get("SECRET_ARN")
database_name = os.environ.get("DATABASE_NAME")

# Initialize Aurora PostgreSQL client
aurora = AuroraPostgres(cluster_arn, database_name, credentials_arn)

# Verify Aurora Cluster conectivity:
aurora.execute_statement("select count(*) from bedrock_integration.knowledge_bases")


def retrieve(event):
    # Extract information from the event
    video_id = event.get("video_id")
    content_type = event.get("content_type")
    query = event.get("query", "hola")
    how = event.get("how", "cosine")
    k = event.get("k", 5)
    
    filter = []
    if video_id: filter.append(dict(key="source", value=video_id))
    if content_type: filter.append(dict(key="content_type", value=event.get("content_type")))

    retriever = CustomMultimodalRetriever(aurora_cluster=aurora, how=how, k=k)
    docs  = retriever.invoke(input=query, filter=filter)
    return docs


def retrieve_generate(event):
    model_id = event.get("model_id", "us.amazon.nova-pro-v1:0")
    query = event.get("query", "hola")
    docs  = retrieve(event)
    parsed_docs = parse_docs_for_context(docs)
    llm = ThinkingLLM(model_id=model_id)

    user_message = f"""Answer the user's questions based on the below context. 
If the context doesn't contain any relevant information to the question, don't make something up and just say "I don't know". 
BTW, IF YOU MAKE SOMETHING UP BY YOUR OWN YOU WILL BE FIRED. 
For each statement in your response provide a [document_number] where n is the document number that provides the response. Dont include the actual content, just the [document_number].

<question>
{query}
</question>

<docuemnts>
"""
    llm_response = llm.answer([text_content_block(user_message), *parsed_docs, text_content_block("</documents>")])

    return {"docs":docs, "response":llm_response[0].get("text")}


def process_event(api_event):
    # Extract information from the event
    body = api_event.get("body", "{}")
    if not body:
        body = "{}"
    body = json.loads(body)
    return body


def lambda_handler(api_event, context):

    print("Received event:", json.dumps(api_event))
    
    # Process the API Gateway event to extract the body
    event = process_event(api_event)
    print("Processed event body:", json.dumps(event))
    
    method = event.get("method", "retrieve")

    try:
        if method == "retrieve":
            docs = retrieve(event)
            docs_json = json.dumps({"docs": [json.loads(doc.model_dump_json()) for doc in docs] })
            
            # Return the response
            response = build_response(200, docs_json)
            print (response)
            return response
        
        elif method == "retrieve_generate":

            response_and_docs = retrieve_generate(event)
            llm_response = response_and_docs.get("response")
            docs = response_and_docs.get("docs")
            docs_json = json.dumps({"docs": [json.loads(doc.model_dump_json()) for doc in docs] })
            response_json = json.dumps({"response": llm_response, "docs": docs_json})

            # Return the response
            response = build_response(200, response_json)
            print (response)
            return response
        else:
            return build_response(400, json.dumps({"message": "Invalid method"}))

    except Exception as e:
        print(f"Error processing results: {str(e)}")
        return build_response(500, 
            json.dumps( {"message": f"Error: {str(e)}", "event": event}))


