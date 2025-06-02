import boto3
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BedrockProcessor:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "amazon.nova-pro-v1:0"
    
    def refine_textract_output(self, raw_text: str) -> str:
        prompt = self._create_refinement_prompt(raw_text)
        
        try:
            response = self._invoke_nova_pro(prompt)
            refined_text = self._extract_refined_text(response)
            logger.info("Texto refinado com sucesso usando Bedrock Nova Pro")
            return refined_text
        except Exception as e:
            logger.error(f"Erro ao refinar texto com Bedrock: {str(e)}")
            return raw_text
    
    def _create_refinement_prompt(self, raw_text: str) -> str:
        return f"""
Você é um especialista em processamento de notas fiscais eletrônicas brasileiras. 
Seu objetivo é refinar e corrigir o texto extraído via OCR de uma nota fiscal, 
mantendo todas as informações importantes e corrigindo erros de reconhecimento de caracteres.

INSTRUÇÕES:
1. Corrija erros comuns de OCR (caracteres mal interpretados)
2. Organize o texto de forma mais estruturada
3. Mantenha TODAS as informações numéricas (CNPJ, CPF, valores, datas, números de série)
4. Corrija nomes de empresas quando possível
5. Mantenha a estrutura lógica de uma nota fiscal
6. NÃO invente informações que não estejam no texto original
7. Retorne apenas o texto refinado, sem explicações adicionais

TEXTO ORIGINAL DA NOTA FISCAL:
{raw_text}

TEXTO REFINADO:
"""
    def _invoke_nova_pro(self, prompt: str) -> Dict[str, Any]:
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 2048,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType='application/json'
        )
        
        return json.loads(response['body'].read())
    
    def _extract_refined_text(self, response: Dict[str, Any]) -> str:
        try:
            content = response['output']['message']['content'][0]['text']
            return content.strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Erro ao extrair texto da resposta do Bedrock: {str(e)}")
            raise Exception("Formato de resposta inesperado do Bedrock")