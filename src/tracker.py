import os
import re
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
        "seletor_preco": "json-ld",
        "render_js": False
    },

    "www.amazon.com.br": {
        "nome_loja": "Amazon",
        "seletor_titulo": "span#productTitle",
        "seletor_preco": "span.a-price-whole",
        "render_js": True
    }

}

# --- Funções Auxiliares ---

# Limpa o nome de um produto para ser um nome de guia válido
def clear_name(name):

    name = re.sub(r'[\\/*?:\[\]]', '', name)
    return name[:100] # Trunca para 100 caracteres, que é o limite do Google Sheets

# --- Google Sheets ---

def get_sheets_client():
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json_str:
        print("  - ERRO: Secret GOOGLE_CREDENTIALS não encontrado.")
        return None
    creds_dict = json.loads(creds_json_str)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    return gspread.service_account_from_dict(creds_dict, scopes=scope)

# Carrega a lista de produtos do Sheets
def load_products(gc):
    try:
        spreadsheet = gc.open("Historico Precos")
        worksheet = spreadsheet.worksheet("Produtos")
        urls = worksheet.col_values(1)[1:]
        print(f"  - {len(urls)} URL(s) encontradas na planilha.")
        return urls
    except Exception as e:
        print(f"  - ERRO ao ler as URLs da planilha: {e}")
    return []

# Salva os dados na planilha
def save_product_data(spreadsheet, product_data, timestamp):
    try:
        sheet_name = clear_name(product_data['title'])

        try:
            product_sheet = spreadsheet.worksheet(sheet_name) # Tenta encontrar a guia do produto
        except gspread.exceptions.WorksheetNotFound:
            print(f"  - Criando nova guia para o produto: '{sheet_name}'") 
            product_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20") # Se não encontrar, cria a guia
            product_sheet.append_row(['Timestamp', 'Preco'])

        # Adiciona a nova linha pesquisada
        product_sheet.append_row([timestamp, product_data['price']])

    except Exception as e:
        print(f"  - ERRO AO SALVAR DADOS: {e}")

# --- ScrapFly ---

# Usa o ScrapFly para buscar a pagina e extrai os dados de um produto
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

def main():
    if not API_KEY or not os.getenv("GOOGLE_CREDENTIALS"):
        print("Erro: Chaves de API não configuradas.")
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Iniciando verificação de preços em {timestamp}")

    google_client = get_sheets_client()
    if not google_client: return

    try:
        spreadsheet = google_client.open("Historico Precos")
    except gspread.exceptions.SpreadsheetNotFound:
        print("ERRO: Planilha 'Historico Precos' não encontrada")
        return

    urls = load_products(google_client) 
    if not urls:
        print("Nenhuma URL para processar. Verificação concluída.")
        return

    for url in urls:
        try:
            domain = urlparse(url).netloc

            if domain not in STORE_CONFIG:
                print(f"AVISO: Loja '{domain}' não configurada")
                continue

            config = STORE_CONFIG[domain]
            print(f"Buscando: {config['nome_loja']} - {url}")
            product_data = scrape_product(url, config)

            if product_data and product_data['price'] is not None:
                save_product_data(spreadsheet, product_data, timestamp) 
                print(f"  -> Sucesso! '{product_data['title']}' - R$ {product_data['price']:.2f}")
            else:
                print("  -> Falha ao encontrar o preço.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao processar a URL {url}: {e}")

    print("Verificação concluída.")

if __name__ == "__main__":
    main()