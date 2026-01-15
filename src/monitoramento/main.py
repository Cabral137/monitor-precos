# Bibliotecas
import os
from datetime import datetime
from urllib.parse import urlparse

# Import dos outros arquivos
from src.core.config import STORE_CONFIG
from src.monitoramento.scraper import scrape_product
from src.core.database import (get_supabase_client, get_produtos, save_preco, get_precos, envio_alerta)

def main():

    # --- Verificações de segurança ---
    if not os.getenv("SCRAPFLY_API_KEY") or not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("Erro: Chaves de API não configuradas.")
        return

    print(f"Iniciando verificação de preços em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    supabase_client = get_supabase_client()
    if not supabase_client: return

    produtos = get_produtos(supabase_client)
    if not produtos: 
        print("Nenhum produto encontrado")
        return

    for item in produtos:
        id_produto = item['id']
        url = item['url']

        try:
            domain = urlparse(url).netloc

            if domain not in STORE_CONFIG:
                print("ERRO: Site não configurado")
                continue

            config = STORE_CONFIG[domain]
            product_data = scrape_product(url, config)

            if product_data and product_data['price'] is not None:
                if save_preco(supabase_client, id_produto, product_data['price']):
                    print(f"{product_data['title']} - {product_data['price']} salvo com suceeso")
            else:
                print(f"Falha ao encontrar o preco do item {product_data['title']}")

            try:
                preco_antigo = get_precos(supabase_client, id_produto)[0]

                if product_data['price'] < preco_antigo:
                    
                    mensagem = "📉 *ALERTA DE QUEDA\!*\n\n"
                    mensagem += f"📦 {product_data['title']}\n\n"
                    mensagem += f"De: ~R$ {preco_antigo:.2f}~\n"
                    mensagem += f"Por: *R$ {product_data['price']:.2f}*\n"
                    
                    envio_alerta(mensagem)

            except Exception as e:
                print(f"ERRO: Não foi possível comparar os preços {e}")

        except Exception as e:
            print(f"ERRO: Ocorreu um erro ao processar {e}")

    print("Análise concluída")

if __name__ == "__main__":
    main()