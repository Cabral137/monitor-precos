import requests
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
import csv

# --- Constantes ---
API_KEY = os.getenv("SCRAPFLY_API_KEY")
PRODUCTS_FILE = os.path.join("data", "products.json")
OUTPUT_FILE = os.path.join("data", "price_history.csv")

def load_products():
    """Carrega a lista de produtos do arquivo JSON."""
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo de produtos '{PRODUCTS_FILE}' não encontrado.")
        return []

def scrape_product_price(url: str, selector: str, render_js: bool):
    """Usa o ScrapFly para buscar o HTML e extrai o preço de um produto."""
    try:
        response = requests.get(
            'https://api.scrapfly.io/scrape',
            params={
                'key': API_KEY,
                'url': url,
                'render_js': render_js,
                'country': 'br',  # Ajuda a obter preços e conteúdo local
            },
            timeout=60 # Aumenta o timeout para requisições com JS
        )
        response.raise_for_status()
        
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        price_element = soup.select_one(selector)
        
        if not price_element:
            return None

        price_text = price_element.get_text(strip=True)
        price_clean = price_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(price_clean)

    except requests.exceptions.RequestException as e:
        print(f"Erro de requisição para {url}: {e}")
        return None
    except (ValueError, TypeError) as e:
        print(f"Erro ao converter o preço para {url}: {e}")
        return None

def save_data(data_row):
    """Salva uma nova linha de dados no arquivo CSV."""
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'nome', 'loja', 'preço']) # Escreve o cabeçalho
        writer.writerow(data_row)

def main():
    """Função principal que orquestra o processo."""
    if not API_KEY:
        print("Erro: Chave de API do ScrapFly não configurada como variável de ambiente.")
        return

    products = load_products()
    if not products:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Iniciando verificação de preços em {timestamp}")

    for product in products:
        print(f"Buscando: {product['nome']} na loja {product['loja']}...")
        price = scrape_product_price(product['url'], product['seletor'], product['render_js'])
        
        if price is not None:
            data_row = [timestamp, product['nome'], product['loja'], price]
            save_data(data_row)
            print(f"  -> Preço encontrado: R$ {price:.2f}")
        else:
            print("  -> Falha ao encontrar o preço.")

    print("Verificação concluída.")

if __name__ == "__main__":
    main()