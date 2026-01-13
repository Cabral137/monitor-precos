import os
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
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verifica se precisaremos do JSON-LD para Título ou Preço
        json_data = None
        if config.get('seletor_titulo') == "json-ld" or config.get('seletor_preco') == "json-ld":
            script_tag = soup.find('script', {'type': 'application/ld+json'})
            if script_tag and script_tag.string:
                try:
                    data = json.loads(script_tag.string)
                    if isinstance(data, list):
                        json_data = next((item for item in data if item.get('@type') == 'Product'), data[0])
                    else:
                        json_data = data
                except json.JSONDecodeError:
                    if debug: print("  -> Erro ao decodificar JSON-LD")

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
                price_clean = (price_text.replace('R$', '')
                               .replace('\xa0', '')
                               .replace(' ', '')
                               .replace('.', '')
                               .replace(',', '.')
                               .strip())
                try:
                    price = float(price_clean)
                except ValueError:
                    pass

        return {'title': title, 'price': price}

    except Exception as e:
        print(f"Erro: {e}")
        return None