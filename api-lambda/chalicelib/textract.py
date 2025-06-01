import boto3
import logging


textract = boto3.client('textract')
logger = logging.getLogger(__name__)

def extract_text(bucket, key):
    """
    Usa Amazon Textract para extrair texto de uma imagem no S3.
    Retorna o texto extraído como string.
    """
    try:
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        lines = [block['Text'] for block in response.get('Blocks', []) if block.get('BlockType') == 'LINE']
        return "\n".join(lines)
    
    except Exception as e:
        logger.exception("Erro ao extrair texto da imagem")
        raise e
