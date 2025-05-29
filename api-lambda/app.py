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
        
        temp_key = f"temp/{original_filename}"
        
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=temp_key,
            Body=image_data,
            ContentType='image/jpeg'
        )

        extracted_text = extract_text(bucket=BUCKET_NAME, key=temp_key)
        parsed_data = parse_invoice_text(extracted_text)
        
        if parsed_data.get("forma_pgto") in ["pix", "dinheiro"]:
            destination_folder = "dinheiro"
        else:
            destination_folder = "outros"
        
        final_key = f"{destination_folder}/{original_filename}"
        
        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={'Bucket': BUCKET_NAME, 'Key': temp_key},
            Key=final_key
        )
        
        s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=temp_key
        )

        return Response(
            status_code=200,
            body={
                "message": f"Imagem salva com sucesso como {final_key}",
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

