import os
import json
import requests
from bs4 import BeautifulSoup

API_KEY = os.getenv("SCRAPFLY_API_KEY")

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