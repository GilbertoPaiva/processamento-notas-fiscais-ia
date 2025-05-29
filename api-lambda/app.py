from chalice import Chalice, Response
import boto3
import uuid
from chalicelib.textract import extract_text
import traceback
from chalicelib.nltk_text import parse_invoice_text

app = Chalice(app_name='consumers')

s3 = boto3.client('s3')
BUCKET_NAME = 'test-sprint-4-5-6'

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

        extracted_text = extract_text(bucket=BUCKET_NAME, key=image_key)
        parsed_data = parse_invoice_text(extracted_text)
        
        if parsed_data.get("forma_pgto") in ["pix", "dinheiro"]:
            destination_folder = "dinheiro"
        else:
            destination_folder = "outros"
        
        json_filename = f"{uuid.uuid4()}.json"
        json_key = f"{destination_folder}/{json_filename}"
        
        import json
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=json_key,
            Body=json.dumps(parsed_data).encode('utf-8'),
            ContentType='application/json'
        )

        return Response(
            status_code=200,
            body={
                "message": f"Processamento concluído com sucesso",
                "imagem": image_key,
                "json": json_key,
                "texto_extraido": parsed_data,
                "pasta_destino": destination_folder
            }
        )

    except Exception as e:
        print('Erro', str(e))
        traceback.print_exc()
        return Response(
            status_code=500,
            body={"error": f"Erro ao salvar imagem: {str(e)}"}
        )

