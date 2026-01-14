# api/webhook.py
import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot

from src.core.database import get_supabase_client, save_produto
from src.monitoramento.scraper import scrape_product
from src.core.config import STORE_CONFIG

app = FastAPI()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
supabase = get_supabase_client()

@app.post("/webhook")
async def process_update(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, bot)

        if update.message and update.message.text:
            text = update.message.text
            chat_id = update.message.chat_id
            
            # Segurança: Apenas você pode adicionar
            if str(chat_id) != os.getenv("TELEGRAM_ID"):
                return {"status": "unauthorized"}

            if text.startswith("/add"):
                parts = text.split(" ")
                if len(parts) < 2:
                    await bot.send_message(chat_id=chat_id, text="Uso: /add <URL>")
                    return {"status": "ok"}

                url = parts[1]
                from urllib.parse import urlparse
                domain = urlparse(url).netloc

                if domain not in STORE_CONFIG:
                    await bot.send_message(chat_id=chat_id, text=f"Loja {domain} não configurada.")
                    return {"status": "ok"}
                
                # Executa o scraper
                product_info = scrape_product(url, STORE_CONFIG[domain])
                
                if product_info and product_info['title'] != "Título não encontrado":
                    # Salva no banco
                    save_produto(supabase, product_info['title'], url)
                    await bot.send_message(chat_id=chat_id, text=f"✅ Monitorando: {product_info['title']}")
                else:
                    await bot.send_message(chat_id=chat_id, text="❌ Não consegui ler o nome do produto.")

        return {"status": "ok"}
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return {"status": "error", "message": str(e)}