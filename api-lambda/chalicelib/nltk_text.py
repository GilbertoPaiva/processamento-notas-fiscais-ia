import re
import nltk



def correct_ocr_errors(text):
    substitutions = {
        r'CMPJ': 'CNPJ',
        r'CONSUMTDOR': 'CONSUMIDOR',
        r'Carted': 'Cartão',
        r'Dt\.Eai\.': 'Dt.Emi.',
        r'FORNA PAGAMENTO': 'FORMA PAGAMENTO',
        r'VALOR PAGA': 'VALOR PAGO',
        r'NFC-e n': 'NFC-e nº ',
        r'Serie:': 'Série:',
    }
    for wrong, right in substitutions.items():
        text = re.sub(wrong, right, text, flags=re.IGNORECASE)
    return text

def parse_invoice_text(text):
    text = correct_ocr_errors(text)
    lines = text.splitlines()

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

    # CNPJ
    cnpj = re.search(r'CNPJ[:\s]*([\d./-]{18})', text)
    if cnpj:
        result["CNPJ_emissor"] = cnpj.group(1)

    # CPF consumidor
    cpf = re.search(r'CPF[:\s]*([\d.-]{14})', text)
    if cpf:
        result["CNPJ_CPF_consumidor"] = cpf.group(1)

    # Data de emissão
    data = re.search(r'Dt\.Emi\.[:\s]*(\d{2}/\d{2}/\d{4})', text)
    if data:
        result["data_emissao"] = data.group(1)
    else:
        fallback_data = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if fallback_data:
            result["data_emissao"] = fallback_data.group(1)

    # Número da nota fiscal
    nf = re.search(r'NFC-e nº?\s*(\d+)', text)
    if nf:
        result["numero_nota_fiscal"] = nf.group(1)

    # Série da nota fiscal
    serie = re.search(r'Série[:\s]*(\d+)', text)
    if serie:
        result["serie_nota_fiscal"] = serie.group(1)

    # Valor total
    valor = re.search(r'Valor Total\s*R\$[\s\n]*([\d.,]+)', text)
    if valor:
        result["valor_total"] = valor.group(1).replace(",", ".")

    # Forma de pagamento
    formas = {
        'dinheiro': ['dinheiro'],
        'pix': ['pix'],
        'cartao': ['cartão', 'credito', 'débito', 'debito'],
        'boleto': ['boleto']
    }

    for forma, palavras in formas.items():
        for palavra in palavras:
            if palavra.lower() in text.lower():
                result["forma_pgto"] = forma
                break
        if result["forma_pgto"]:
            break

    # Nome e endereço do emissor
    for i, line in enumerate(lines):
        if "CNPJ" in line:
            if i >= 1:
                result["endereco_emissor"] = lines[i-1].strip()
            if i >= 2:
                result["nome_emissor"] = lines[i-2].strip()
            break

    return result
