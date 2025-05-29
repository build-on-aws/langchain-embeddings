from utils import read_image_from_s3

def image_content_block(image_file):
    print (image_file)
    image_bytes = read_image_from_s3(image_file)
    extension = image_file.split('.')[-1]
    print (f"Including Image :{image_file}")
    if extension == 'jpg':
        extension = 'jpeg'
    
    block = { "image": { "format": extension, "source": { "bytes": image_bytes}}}
    return block

def text_content_block(text):
    return { "text": text }

def parse_docs_for_context(docs):
    blocks = []
    for doc in docs:
        if doc.metadata.get('content_type') == "image":
            blocks.append(image_content_block(doc.metadata.get("source")))
        else:
            blocks.append(text_content_block(doc.page_content))
    return blocks