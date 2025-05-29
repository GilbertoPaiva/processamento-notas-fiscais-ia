from chalice import Chalice, Response
import boto3
import uuid
from chalicelib.textract import extract_text
import traceback # Verificar erro na aws
from chalicelib.nltk_text import parse_invoice_text

app = Chalice(app_name='consumers')

s3 = boto3.client('s3')
BUCKET_NAME = 'teste-sprint-4-5-6'

@app.route('/api/v1/invoice', methods=['POST'], content_types=['image/jpeg'])
def post_nf():
    try:
        # Obter dados binários do corpo da requisição
        image_data = app.current_request.raw_body

        filename = f"{uuid.uuid4()}.jpg"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=image_data,
            ContentType='image/jpeg'
        )

        extracted_text = extract_text(bucket=BUCKET_NAME, key=filename)
        parsed_data = parse_invoice_text(extracted_text)

        return Response(
            status_code=200,
            body={"message": f"Imagem salva com sucesso como {filename}",
                  "texto_extraido": parsed_data}
        )

    except Exception as e:
        print('Erro', str(e))
        traceback.print_exc()
        return Response(
            status_code=500,
            body={"error": f"Erro ao salvar imagem: {str(e)}"}
        )

