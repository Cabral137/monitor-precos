# Bibliotecas
import os
from datetime import datetime
from urllib.parse import urlparse

# Import dos outros arquivos
from config import STORE_CONFIG
from integrations import (get_sheets_client, load_products, save_product_data)
from scraper import scrape_product

def main():

    # --- Verificações de segurança ---
    if not os.getenv("SCRAPFLY_API_KEY") or not os.getenv("GOOGLE_CREDENTIALS"):
        print("Erro: Chaves de API não configuradas.")
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Iniciando verificação de preços em {timestamp}")

    google_client = get_sheets_client()
    if not google_client: return

    try:
        spreadsheet = google_client.open("Historico Precos")
    except Exception as e:
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