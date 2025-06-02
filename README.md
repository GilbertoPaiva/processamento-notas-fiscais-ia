# Processamento de Notas Fiscais com IA

Projeto de processamento inteligente de notas fiscais utilizando serviços AWS e técnicas de NLP.  
O objetivo é criar uma API REST em Python que recebe uma imagem de nota fiscal eletrônica, armazena a imagem num bucket S3, extrai e refina o texto utilizando o Amazon Textract e recursos de NLP (com NLTK), e armazena os dados estruturados em JSON de acordo com os requisitos.

---

## Descrição do Projeto

A aplicação implementa os seguintes passos:
1. **Recepção da Requisição via API REST:**  
   - A API disponibiliza a rota `POST /api/v1/invoice` para receber um arquivo JPEG (imagem de nota fiscal) via request multiparte (upload).
2. **Armazenamento da Imagem no S3:**  
   - A imagem é salva no bucket S3 na pasta `imagens` com um nome único gerado via UUID.
3. **Extração de Texto com Amazon Textract:**  
   - O serviço Textract é utilizado para extrair o texto da imagem. As linhas detectadas são agrupadas num único texto.
4. **Refinamento do Texto com Amazon Bedrock Nova Pro:**  
   - O texto extraído do Textract é refinado usando o modelo Nova Pro do Amazon Bedrock para corrigir erros de OCR e melhorar a qualidade dos dados antes do processamento com NLTK.
5. **Processamento do Texto com NLTK:**  
   - **Correção de erros de OCR:** Utiliza padrões definidos para corrigir erros comuns.
   - **Tokenização, remoção de stopwords e stemming:** O NLTK normaliza e transforma o texto para facilitar a extração de informações.
   - **Extração de entidades (NER):** Utiliza POS tagging e chunking para identificar entidades como nome do emissor, CNPJ, endereço, data de emissão, número e série da nota, valor total e forma de pagamento.
6. **Armazenamento dos Dados Estruturados:**  
   - Com base na forma de pagamento identificada, os dados extraídos são salvos no S3 em uma pasta de destino: notas pagas em dinheiro ou pix (pasta `dinheiro`) ou outras formas (pasta `outros`).
7. **Logs via CloudWatch:**  
   - Toda a execução da função Lambda gera logs que podem ser acompanhados no CloudWatch para monitoramento e debugging.

---

## Arquitetura Básica

- **API REST:** Implementada utilizando [Chalice](https://chalice.readthedocs.io/) para facilitar a criação e deploy de funções Lambda.
- **Bucket S3:** Armazena as imagens recebidas e os arquivos JSON com as informações extraídas.
- **Amazon Textract:** Realiza a detecção de texto nas imagens.
- **Amazon Bedrock (Nova Pro):** Refina e corrige o texto extraído do Textract, melhorando a qualidade dos dados antes do processamento NLP.
- **NLTK:** Processa o texto refinado, aplicando técnicas de NLP para extração de informações relevantes.
- **CloudWatch Logs:** As funções Lambda registram logs para facilitar o acompanhamento da execução e resolução de problemas.

---

## Instalação

### Pré-requisitos
- Python 3.12
- AWS CLI configurado com as credenciais necessárias para deploy na AWS
- Chalice instalado (pip install chalice)

### Passos

1. **Clone este repositório:**
   ```bash
   git clone https://github.com/GilbertoPaiva/processamento-notas-fiscais-ia.git
   cd processamento-notas-fiscais-ia
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate (para Linux/Mac)
   venv\Scripts\activate (para Windows)
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r api-lambda/requirements.txt
   ```

4. **Configurar o Amazon Bedrock:**
   
   1. **Habilitar o modelo Nova Pro:**
      - Acesse o console do Amazon Bedrock na região us-east-1
      - Vá para "Model access" no painel lateral
      - Encontre o modelo "Nova Pro" (amazon.nova-pro-v1:0)
      - Clique em "Request model access" e aguarde a aprovação
   
   2. **Configurar permissões IAM:**
      - A role da função Lambda precisa ter permissão para usar o Bedrock
      - Adicione a política com as seguintes permissões:
        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "arn:aws:bedrock:*:*:model/amazon.nova-pro-v1:0"
                }
            ]
        }
        ```

5. **Gerar e Aplicar a Layer do NLTK via AWS Console:**

   1. **Preparar os arquivos da layer localmente:**
      - Crie uma estrutura de diretórios que simule a raiz padrão do Python. Por exemplo, num ambiente Linux/WSL:
        ```bash
        mkdir -p nltk_layer/python/lib/python3.12/site-packages
        export LAYER_PATH=~/nltk_layer/python/lib/python3.12/site-packages
        ```
      - Instale o NLTK na pasta da layer:
        ```bash
        pip install --upgrade --target="$LAYER_PATH" nltk>=3.9.1
        ```
      - Baixe os recursos necessários do NLTK (tokenizers, corpora, taggers, chunkers, stemmers). Exemplo:
        ```python
        import os
        import nltk
        download_dir = os.path.join(os.environ["LAYER_PATH"], "nltk_data")
        nltk.download('punkt_tab', download_dir=download_dir)
        nltk.download('stopwords', download_dir=download_dir)
        nltk.download('words', download_dir=download_dir)
        nltk.download('averaged_perceptron_tagger_eng', download_dir=download_dir)
        nltk.download('maxent_ne_chunker_tab', download_dir=download_dir)
        nltk.download('rslp', download_dir=download_dir)
        exit()
        ```
      - Verifique que a estrutura interna esteja correta, por exemplo, com os diretórios `nltk_data/tokenizers`, `nltk_data/corpora`, `nltk_data/taggers`, etc.

   2. **Compactar a Layer:**
      - Navegue até a pasta `nltk_layer` e compacte todo o conteúdo:
        ```bash
        cd ~/nltk_layer
        zip -r ../nltk_layer.zip .
        cd ~
        ```
   
   3. **Criar a Layer no Console AWS:**
      - Faça login no AWS Management Console e acesse o serviço AWS Lambda.
      - No painel lateral, clique em “Layers” e escolha “Create layer”.
      - Preencha um nome para a layer (por exemplo, `nltk_layer`), adicione uma descrição se desejar e, em “Upload a .zip file”, selecione o arquivo `nltk_layer.zip`.
      - Selecione o runtime apropriado (por exemplo, Python 3.12) e clique em “Create”.

   4. **Aplicar a Layer na Função Lambda:**
      - No console da AWS Lambda, abra a função que utiliza o NLTK.
      - Na seção “Layers”, clique em “Add a layer” e selecione “Custom layers”.
      - Escolha a layer `nltk_layer` que você acabou de criar e selecione a versão desejada.
      - Salve as alterações.

   5. **Ajustar o Código (se necessário):**
      - Certifique-se de que no código o NLTK procura os dados na camada, por exemplo:
        ```python
        import nltk
        nltk.data.path.append('/opt/python/lib/python3.12/site-packages/nltk_data')
        ```
      - Dessa forma, a função Lambda encontrará os recursos do NLTK dentro da layer.

---

## Utilização

### Deploy da API
Realize o deploy da função Lambda com:
```bash
cd api-lambda
chalice deploy
```
O comando retornará a URL da API. Por exemplo:
```
https://0bcvfntv75.execute-api.us-east-1.amazonaws.com/api/api/v1/invoice
```

### Uso da API
Envie uma requisição POST para `/api/v1/invoice` com o corpo contendo o arquivo da nota fiscal (formato `image/jpeg`).  
Exemplo com cURL:
```bash
curl --location --request POST 'https://0bcvfntv75.execute-api.us-east-1.amazonaws.com/api/api/v1/invoice' \
--form 'file=@"path/to/nota.jpg"'
```

### Resposta
A API retornará uma resposta JSON com os seguintes campos:
- **nome_emissor:** Nome do fornecedor identificado
- **CNPJ_emissor:** CNPJ do emissor
- **endereco_emissor:** Endereço extraído
- **CNPJ_CPF_consumidor:** CNPJ/CPF do consumidor (caso identificado)
- **data_emissao:** Data de emissão
- **numero_nota_fiscal:** Número da nota fiscal (se identificado)
- **serie_nota_fiscal:** Série da nota fiscal (se identificado)
- **valor_total:** Valor total da nota
- **forma_pgto:** Forma de pagamento (dinheiro, pix ou outros)

Exemplo:
```json
{
    "message": "Processamento concluído com sucesso",
    "imagem": "imagens/6ec5b40a-4852-43b3-8a04-657443ac8051.jpg",
    "json": "dinheiro/6a33c6f7-a863-4c11-8e07-7671776d3bae.json",
    "texto_extraido": {
        "nome_emissor": "STARBUCKS",
        "CNPJ_emissor": "00.000.000/0001-00",
        "endereco_emissor": "BAIRRO: CARLANDS CEP: 88047-902 FLORIANOPOLIS-SC",
        "CNPJ_CPF_consumidor": "000,000,000-0",
        "data_emissao": "26/10/2020",
        "numero_nota_fiscal": "123456789",
        "serie_nota_fiscal": "123",
        "valor_total": "10.90",
        "forma_pgto": "dinheiro"
    },
    "pasta_destino": "dinheiro"
}
```

---

## Considerações Finais

- **Logs e Monitoramento:** Toda a execução da API é registrada no CloudWatch. Verifique os logs para identificar detalhes de execução ou possíveis erros.
- **Organização do Projeto:**  
  - *api-lambda*: Contém a aplicação e arquivos de configuração do Chalice.
  - *chalicelib*: Agrupa os módulos de processamento (Textract, NLTK).
  - *nltk_layer*: (Gerada separadamente) contém os recursos do NLTK necessários para o processamento.

- **Dificuldades Conhecidas:**  
  - Integração de recursos do NLTK em ambientes AWS Lambda pode exigir camadas personalizadas.
  - A extração de certas informações pode ser sensível à formatação da nota fiscal.

---

## URL da API
Após o deploy, a URL será exibida no terminal. Utilize essa URL para testar a API, por exemplo, via cURL ou Postman.

---

## Equipe

- [Alexandre Castejon]
- [Cleison Rocha Xavier]
- [Gilberto de Paiva Melo]

---

**