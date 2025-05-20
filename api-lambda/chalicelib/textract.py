import boto3


textract = boto3.client('textract')

def extract_text(bucket, key):
    """
    Usa Amazon Textract para extrair texto de uma imagem no S3.
    Retorna o texto extraído como string.
    """
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )

    extracted_text = ""
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            extracted_text += block['Text'] + '\n'

    return extracted_text
