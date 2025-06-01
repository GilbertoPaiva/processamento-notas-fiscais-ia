import nltk
nltk.data.path.append('/opt/python/lib/python3.12/site-packages/nltk_data')

import re
import string
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
from functools import lru_cache

@lru_cache(maxsize=32)
def correct_ocr_errors(text):
    substitutions = {
        r'CMPJ': 'CNPJ',
        r'CONSUMTDOR': 'CONSUMIDOR',
        r'Carted': 'Cartão',
        r'Dt\.Eai\.': 'Dt.Emi.',
        r'FORNA PAGAMENTO': 'FORMA PAGAMENTO',
        r'VALOR PAGA': 'VALOR PAGO',
        r'NFC-e n': 'NFC-e nº ',
        r'Serie:': 'Série:'
    }
    for wrong, right in substitutions.items():
        text = re.sub(wrong, right, text, flags=re.IGNORECASE)
    return text

def normalize_and_tokenize(text):
    tokens = word_tokenize(text.lower())
    # Remoção de pontuação
    return [t for t in tokens if t not in string.punctuation]

def remove_stopwords(tokens):
    stop_words = set(stopwords.words('portuguese'))
    return [t for t in tokens if t not in stop_words]

def stem_tokens(tokens):
    stemmer = RSLPStemmer()
    return [stemmer.stem(token) for token in tokens]

def extract_entities(text):
    # Aplica correção e tokenização básica uma única vez
    clean_text = correct_ocr_errors(text)
    sentences = sent_tokenize(clean_text, language='portuguese')
    entities = {"ORGANIZATION": [], "GPE": [], "PERSON": []}
    for sentence in sentences:
        tokens = word_tokenize(sentence)
        # Obrigatório para o pos_tag usar o modelo inglês (averaged_perceptron_tagger_eng)
        tags = pos_tag(tokens, lang='eng')
        tree = ne_chunk(tags)
        for subtree in tree.subtrees():
            if subtree.label() in entities:
                entity = " ".join(word for word, tag in subtree.leaves())
                entities[subtree.label()].append(entity)
    return entities

def extract_invoice_data_nltk(text):
    # Aplica a correção do OCR uma única vez
    text = correct_ocr_errors(text)
    lines = text.splitlines()
    
    # Tokeniza o texto uma vez para evitar chamadas repetidas
    tokens = word_tokenize(text)
    lower_text = text.lower()
    
    # Extrai entidades usando função otimizada
    entities = extract_entities(text)
    
    result = {
        "nome_emissor": None,
        "CNPJ_emissor": None,
        "endereco_emissor": None,
        "CNPJ_CPF_consumidor": None,
        "data_emissao": None,
        "numero_nota_fiscal": None,
        "serie_nota_fiscal": None,
        "valor_total": None,
        "forma_pgto": None
    }

    # Nome do emissor via NER (Organization)
    if entities["ORGANIZATION"]:
        result["nome_emissor"] = entities["ORGANIZATION"][0]

    # Endereço: heurística usando linha anterior ao "CNPJ" ou entidade geopolítica (GPE)
    for i, line in enumerate(lines):
        if "CNPJ" in line and i >= 1:
            result["endereco_emissor"] = lines[i-1].strip()
            break
    if not result["endereco_emissor"] and entities["GPE"]:
        result["endereco_emissor"] = entities["GPE"][0]

    # Extração de CNPJ/CPF – simples busca por tokens
    for i, token in enumerate(tokens):
        if token == "CNPJ" and i + 1 < len(tokens):
            result["CNPJ_emissor"] = tokens[i+1]
        if token == "CPF" and i + 1 < len(tokens):
            result["CNPJ_CPF_consumidor"] = tokens[i+1]

    # Data de emissão: busca por token com formatação de data (dd/mm/yyyy)
    for token in tokens:
        if token.count('/') == 2 and len(token) == 10:
            result["data_emissao"] = token
            break

    # Número e série da nota fiscal
    for i, token in enumerate(tokens):
        if "NFC-e" in token and i + 1 < len(tokens):
            result["numero_nota_fiscal"] = tokens[i+1]
        if "Série" in token and i + 1 < len(tokens):
            result["serie_nota_fiscal"] = tokens[i+1]

    # Valor total: busca nos tokens subsequentes à palavra "total" ou "valor"
    for i, token in enumerate(tokens):
        if token.lower() in ["total", "valor"]:
            for j in range(i, min(i+4, len(tokens))):
                if tokens[j].replace('.', '').replace(',', '').isdigit():
                    valor = tokens[j].replace(",", ".")
                    result["valor_total"] = valor
                    break
            if result["valor_total"]:
                break

    # Forma de pagamento: análise semântica simples usando lower_text
    formas = {
        'dinheiro': ['dinheiro'],
        'pix': ['pix'],
        'cartao': ['cartão', 'credito', 'débito', 'debito'],
        'boleto': ['boleto']
    }
    for forma, palavras in formas.items():
        for palavra in palavras:
            if palavra in lower_text:
                result["forma_pgto"] = forma
                break
        if result["forma_pgto"]:
            break

    # Exemplo adicional: tokenização, remoção de stopwords e stemming (executado uma única vez)
    tokens_norm = normalize_and_tokenize(text)
    tokens_sem_stop = remove_stopwords(tokens_norm)
    tokens_stem = stem_tokens(tokens_sem_stop)
    # Os tokens_stem podem ser usados para análises textuais adicionais, se necessário

    return result
