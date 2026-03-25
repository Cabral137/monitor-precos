# --- Dicionário ---
STORE_CONFIG = {

    "www.kabum.com.br": {
        "nome_loja": "Kabum",
        "seletor_titulo": "json-ld",
        "seletor_preco": "json-ld",
        "render_js": False
    },

    "www.amazon.com.br": {
        "nome_loja": "Amazon",
        "seletor_titulo": "#productTitle",
        "seletor_preco": "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
        "render_js": False
    },

    "www.mercadolivre.com.br": {
        "nome_loja": "Mercado Livre",
        "seletor_titulo": ".ui-pdp-title",
        "seletor_preco": ".ui-pdp-price__second-line .andes-money-amount",
        "render_js": False
    },

    "www.magazineluiza.com.br": {
        "nome_loja": "Magazine Luiza",
        "seletor_titulo": "h1[data-testid='heading-product-title']",
        "seletor_preco": "[data-testid='price-value']",
        "render_js": False
    }

}
