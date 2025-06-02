import json
import uuid
import logging
import traceback

from chalice import Chalice, Response
import boto3

from chalicelib.textract import extract_text
from chalicelib.bedrock_processor import BedrockProcessor
from chalicelib.nltk_text import extract_invoice_data_nltk

app = Chalice(app_name='consumers')
logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
BUCKET_NAME = 'invoice-processing-bucket'

@app.route('/api/v1/invoice', methods=['POST'], content_types=['image/jpeg'])
def post_nf():
    try:
        image_data = app.current_request.raw_body
        original_filename = f"{uuid.uuid4()}.jpg"
        image_folder = "imagens"
        image_key = f"{image_folder}/{original_filename}"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=image_key,
            Body=image_data,
            ContentType='image/jpeg'
        )
        logger.info(f"Imagem salva em: {image_key}")

        extracted_text = extract_text(bucket=BUCKET_NAME, key=image_key)
        
        bedrock_processor = BedrockProcessor()
        refined_text = bedrock_processor.refine_textract_output(extracted_text)
        logger.info("Texto refinado com Bedrock Nova Pro")
        
        parsed_data = extract_invoice_data_nltk(refined_text)
        
        if parsed_data.get("forma_pgto") in ["pix", "dinheiro"]:
            destination_folder = "dinheiro"
        else:
            destination_folder = "outros"
        
        json_filename = f"{uuid.uuid4()}.json"
        json_key = f"{destination_folder}/{json_filename}"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=json_key,
            Body=json.dumps(parsed_data).encode('utf-8'),
            ContentType='application/json'
        )
        logger.info(f"JSON salvo em: {json_key}")

        return Response(
            status_code=200,
            body={
                "message": "Processamento concluído com sucesso",
                "imagem": image_key,
                "json": json_key,
                "texto_extraido": parsed_data,
                "pasta_destino": destination_folder
            }
        )

    except Exception as e:
        logger.error("Erro ao processar a imagem", exc_info=True)
        return Response(
            status_code=500,
            body={"error": f"Erro ao salvar imagem: {str(e)}"}
        )

