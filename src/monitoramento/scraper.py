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
                'asp': True,
            },
            timeout=90
        )
        response.raise_for_status()
        
        html_content = response.json().get('result', {}).get('content', '')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verifica se precisaremos do JSON-LD para Título ou Preço
        json_data = None
        if config.get('seletor_titulo') == "json-ld" or config.get('seletor_preco') == "json-ld":
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                if script and script.string:
                    try:
                        data = json.loads(script.string)
                        # Trata se o JSON for uma lista
                        if isinstance(data, list):
                            for item in data:
                                if item.get('@type') == 'Product':
                                    json_data = item
                                    break
                        # Trata se o JSON for um dicionário
                        elif isinstance(data, dict):
                            if '@graph' in data:
                                for item in data['@graph']:
                                    if item.get('@type') == 'Product':
                                        json_data = item
                                        break
                            elif data.get('@type') == 'Product':
                                json_data = data
                                
                        if json_data:
                            break
                    except json.JSONDecodeError:
                        continue

        # --- 1. Extração do Título ---
        title = "Título não encontrado"
        seletor_titulo = config.get('seletor_titulo')

        if seletor_titulo == "json-ld" and json_data:
            title = json_data.get('name', title)
            
        elif seletor_titulo and seletor_titulo != "json-ld":
            el = soup.select_one(seletor_titulo)
            if el: title = el.get_text(strip=True)

        # --- 2. Extração do Preço ---
        price = None
        seletor_preco = config.get('seletor_preco')

        if seletor_preco == "json-ld" and json_data:
            offers = json_data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
                
            price_str = offers.get('price')
            if price_str:
                price = float(price_str)
                
        elif seletor_preco and seletor_preco != "json-ld":
            el = soup.select_one(seletor_preco)

            if el:
                price_text = el.get_text(strip=True)
                
                price_clean = re.sub(r'[^\d,.]', '', price_text)
                
                if price_clean:
                    # Lógica de conversão segura
                    if ',' in price_clean and '.' in price_clean:
                        price_clean = price_clean.replace('.', '').replace(',', '.')
                    elif ',' in price_clean:
                        price_clean = price_clean.replace(',', '.')
                        
                    try:
                        price = float(price_clean)
                    except ValueError:
                        pass

            return {'title': title, 'price': price}

    except Exception as e:
        print(f"Erro: {e}")
        return None