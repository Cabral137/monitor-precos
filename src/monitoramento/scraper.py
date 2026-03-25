import os
import re
import json
import requests
from bs4 import BeautifulSoup

API_KEY = os.getenv("SCRAPFLY_API_KEY")


def scrape_product(url: str, config: dict, debug: bool = False):
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
        
        html_content = response.json().get('result', {}).get('content', '')
        if debug: print(f"  -> HTML content length: {len(html_content)}")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verifica se precisaremos do JSON-LD para Título ou Preço
        json_data = None
        if config.get('seletor_titulo') == "json-ld" or config.get('seletor_preco') == "json-ld":
            if debug: print("  -> Buscando JSON-LD...")
            script_tag = soup.find('script', {'type': 'application/ld+json'})
            if script_tag and script_tag.string:
                try:
                    if debug: print("  -> JSON-LD encontrado, decodificando...")
                    data = json.loads(script_tag.string)
                    if isinstance(data, list):
                        json_data = next((item for item in data if item.get('@type') == 'Product'), data[0])
                    else:
                        json_data = data
                    if debug: print(f"  -> JSON-LD Data: {json.dumps(json_data, indent=2)}")
                except json.JSONDecodeError:
                    if debug: print("  -> Erro ao decodificar JSON-LD")
            else:
                if debug: print("  -> Tag script JSON-LD não encontrada.")

        # --- 1. Extração do Título ---
        title = "Título não encontrado"
        seletor_titulo = config.get('seletor_titulo')
        if debug: print(f"  -> Extraindo título com seletor: '{seletor_titulo}'")

        if seletor_titulo == "json-ld":
            if json_data:
                title = json_data.get('name', title)
                if debug: print(f"  -> Título do JSON-LD: '{title}'")
            else:
                if debug: print("  -> Seletor de título é JSON-LD, mas nenhum dado JSON-LD foi encontrado.")
        elif seletor_titulo:
            el = soup.select_one(seletor_titulo)
            if el:
                title = el.get_text(strip=True)
                if debug: print(f"  -> Título do seletor CSS: '{title}'")
            else:
                if debug: print("  -> Seletor de título CSS não encontrou nenhum elemento.")

        # --- 2. Extração do Preço ---
        price = None
        seletor_preco = config.get('seletor_preco')
        if debug: print(f"  -> Extraindo preço com seletor: '{seletor_preco}'")

        if seletor_preco == "json-ld":
            if json_data:
                offers = json_data.get('offers', {})
                if debug: print(f"  -> Offers do JSON-LD: {offers}")

                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                
                price_str = offers.get('price')
                if debug: print(f"  -> String de preço do JSON-LD: '{price_str}'")

                if price_str:
                    try:
                        price = float(price_str)
                    except (ValueError, TypeError):
                        if debug: print("  -> Não foi possível converter o preço do JSON-LD para float.")
            else:
                if debug: print("  -> Seletor de preço é JSON-LD, mas nenhum dado JSON-LD foi encontrado.")
                
        elif seletor_preco:
            el = soup.select_one(seletor_preco)
            if el:
                price_text = el.get_text(strip=True)
                if debug: print(f"  -> Texto do preço do seletor CSS: '{price_text}'")
                
                price_clean = re.sub(r'[^\d,.]', '', price_text)
                
                if price_clean:
                    if ',' in price_clean and '.' in price_clean:
                        price_clean = price_clean.replace('.', '').replace(',', '.')
                    elif ',' in price_clean:
                        price_clean = price_clean.replace(',', '.')
                        
                    try:
                        price = float(price_clean)
                        if debug: print(f"  -> Preço convertido: {price}")
                    except ValueError:
                        if debug: print("  -> Não foi possível converter o preço limpo para float.")
                else:
                    if debug: print("  -> String de preço limpa está vazia.")
            else:
                if debug: print("  -> Seletor de preço CSS não encontrou nenhum elemento.")
        
        return {'title': title, 'price': price}

    except requests.exceptions.RequestException as e:
        print(f"ERRO DE REDE ao acessar ScrapFly: {e}")
        return None
    except Exception as e:
        print(f"ERRO INESPERADO no scraper: {e.__class__.__name__}: {e}")
        # Adiciona um traceback para depuração mais profunda, se necessário
        # import traceback
        # traceback.print_exc()
        return None