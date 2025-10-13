import os
import csv
import json
import gspread
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

# --- Constantes ---
API_KEY = os.getenv("SCRAPFLY_API_KEY")
PRODUCTS_FILE = os.path.join("data", "products.json")
OUTPUT_FILE = os.path.join("data", "price_history.csv")

# --- Dicionário ---
STORE_CONFIG = {

    "www.kabum.com.br": {
        "nome_loja": "Kabum",
        "seletor_titulo": "h1.sc-a1f7a75-1",
        "seletor_preco": "json_ld",
        "render_js": True
    },

    "www.amazon.com.br": {
        "nome_loja": "Amazon",
        "seletor_titulo": "span#productTitle",
        "seletor_preco": "span.a-price-whole",
        "render_js": True
    }

}

# Carrega a lista de produtos do arquivo JSON
def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    except FileNotFoundError:
        print(f"Erro: Arquivo de produtos '{PRODUCTS_FILE}' não encontrado.")
        return []

# Usa o ScrapFly para buscar dados e extrai os dados de um produto
def scrape_product (url: str, config: dict):
    try:
        print(f"  - Usando render_js: {config['render_js']}")
        response = requests.get(
            'https://api.scrapfly.io/scrape',
            params={
                'key': API_KEY,
                'url': url,
                'render_js': config['render_js'],
                'country': 'br',
            },
            timeout=90
        )
        response.raise_for_status()

        # Extração do HTML do site
        api_response = response.json() # 1. Analisa a resposta completa do ScrapFly como JSON
        html_content = api_response.get('result', {}).get('content', '') # 2. Pega o conteúdo HTML de dentro do JSON
        soup = BeautifulSoup(html_content, 'html.parser') # 3. BeautifulSoup analisa apenas o HTML correto
        
        # Extração do nome do produto
        title = "Título não encontrado" # Define um valor padrão
        title_selector = config.get('seletor_titulo') # Pega o seletor de forma segura

        if title_selector: # 1. Só continua se o seletor não for vazio
            title_element = soup.select_one(title_selector)
            if title_element: # 2. Só extrai o texto se o elemento foi encontrado
                title = title_element.get_text(strip=True)

        # Extração do preço do produto
        price = None
        price_selector = config.get('seletor_preco')

        if price_selector == "json-ld": # Area com dados JSON no HTML do site

            script_tag = soup.find('script', {'type': 'application/ld+json'})
            if script_tag and script_tag.string:
                json_data = json.loads(script_tag.string)
                price_str = json_data.get('offers', {}).get('price')
                
                if price_str:
                    price = float(price_str)

        elif price_selector: # Se for um seletor CSS e não for vazio

            price_element = soup.select_one(price_selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                price_clean = price_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
                price = float(price_clean)
        
        return {'title': title, 'price': price}

    except requests.exceptions.RequestException as e:
        print(f"  - ERRO de requisição para {url}: {e}")
        return None
    except (ValueError, TypeError, json.JSONDecodeError, KeyError) as e:
        print(f"  - ERRO ao processar o dado para {url}: {e}")
        return None

# Salva uma nova linha de dados em uma planilha do Google Sheets
def save_data(data_row):

    try:
        # Pega as credenciais do Secret do GitHub
        creds_json_str = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_json_str:
            print("  - ERRO: Secret GOOGLE_CREDENTIALS não encontrado.")
            return

        creds_dict = json.loads(creds_json_str)
        
        # Define o escopo de permissões
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Autentica usando as credenciais
        gc = gspread.service_account_from_dict(creds_dict, scopes=scope)
        
        # Abre a planilha pelo nome e seleciona a primeira aba (worksheet)
        spreadsheet = gc.open("Historico Precos") 
        worksheet = spreadsheet.sheet1

        # Adiciona o cabeçalho se a planilha estiver vazia
        if not worksheet.get_all_records():
             worksheet.append_row(['timestamp', 'nome', 'loja', 'preco'])

        # Adiciona a linha de dados
        worksheet.append_row(data_row)
        
    except gspread.exceptions.SpreadsheetNotFound:
        print("  - ERRO: Planilha 'Historico Precos' não encontrada.")
    except Exception as e:
        print(f"  - ERRO ao salvar no Google Sheets: {e}")

def main():
    if not API_KEY:
        print("Erro: Chave de API do ScrapFly não configurada.")
        return

    urls = load_products() 
    if not urls:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Iniciando verificação de preços em {timestamp}")

    for url in urls:
        try:
            domain = urlparse(url).netloc

            if domain not in STORE_CONFIG:
                print(f"AVISO: Loja com domínio '{domain}' não configurada. Pulando URL: {url}")
                continue

            config = STORE_CONFIG[domain]
            print(f"Buscando: {config['nome_loja']} - {url}")

            product_data = scrape_product(url, config)

            if product_data and product_data['price'] is not None:
                price = product_data['price']
                title = product_data['title']
                store_name = config['nome_loja']

                data_row = [timestamp, title, store_name, price]
                save_data(data_row) 

                print(f"  -> Sucesso! '{title}' - R$ {price:.2f}")
            else:
                print("  -> Falha ao encontrar o preço.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao processar a URL {url}: {e}")

    print("Verificação concluída.")

if __name__ == "__main__":
    main()