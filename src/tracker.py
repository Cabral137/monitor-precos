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

# Carrega a lista de produtos do arquivo JSON
def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo de produtos '{PRODUCTS_FILE}' não encontrado.")
        return []

# Usa o ScrapFly para buscar o HTML e extrai o preço de um produto
def scrape_product_price(url: str, selector: str, render_js: bool):
    try:
        print(f"  - Usando render_js: {render_js}")
        response = requests.get(
            'https://api.scrapfly.io/scrape',
            params={
                'key': API_KEY,
                'url': url,
                'render_js': render_js,
                'country': 'br',
            },
            timeout=90
        )
        response.raise_for_status()

        # --- SALVANDO O ARQUIVO DE DEBUG ---
        output_html_file = 'scrapfly_output.html'
        with open(output_html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"  - !!! O HTML recebido pelo ScrapFly foi salvo em '{output_html_file}' !!!")
        # -----------------------------------------------------------
        
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        price_element = soup.select_one(selector)
        
        if not price_element:
            print(f"  - ERRO: Seletor CSS '{selector}' não encontrado no HTML recebido.")
            return None

        price_text = price_element.get_text(strip=True)
        price_clean = price_text.replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(price_clean)

    except requests.exceptions.RequestException as e:
        print(f"  - ERRO de requisição para {url}: {e}")
        return None
    except (ValueError, TypeError) as e:
        print(f"  - ERRO ao processar o dado para {url}: {e}")
        return None

# Salva uma nova linha de dados no arquivo CSV.
def save_data(data_row):
    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'nome', 'loja', 'preço']) # Escreve o cabeçalho
        writer.writerow(data_row)

def main():

    if not API_KEY:
        print("Erro: Chave de API do ScrapFly não configurada como variável de ambiente.")
        return

    products = load_products()
    if not products:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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