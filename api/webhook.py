# api/webhook.py
import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from urllib.parse import urlparse

from src.core.database import get_supabase_client, save_produto, get_produtos, delete_produto, get_precos
from src.monitoramento.scraper import scrape_product
from src.core.config import STORE_CONFIG

app = FastAPI()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ID")
bot = Bot(token=TOKEN)
supabase = get_supabase_client()

# --- Comandos ---

async def add (chat_id, args):

    if not args:
        await bot.send_message(chat_id, "Uso: /add <URL>")
        return

    # Somente o Admin pode adicionar
    if str(chat_id) != ADMIN_ID:
        await bot.send_message(chat_id, "Você não tem permissão para adicionar produtos")
        return
    
    url = args[0]
    dominio = urlparse(url).netloc

    if dominio not in STORE_CONFIG:
        await bot.send_message(chat_id, "Site não configurado")
        return 
    
    product_info = scrape_product(url, STORE_CONFIG[dominio])

    if product_info and  product_info['title'] != "Título não encontrado":
        save_produto(supabase, product_info['title'], url)
        await bot.send_message(chat_id, "Produto adicionado com sucesso")

    else:
        await bot.send_message(chat_id, "Não foi possível adicionar o produto")


async def list (chat_id):
    
    produtos = get_produtos(supabase)

    if produtos:

        if not produtos:
            await bot.send_message(chat_id, "Nenhum produto encontrado")
            return

        mensagem = "📋 *Produtos Monitorados*\n\n"

        for item in produtos:
            mensagem += f"🆔 ID: `{item['id']}`\n"
            mensagem += f"📦 *{item['nome']}*\n"
            mensagem += f"🔗 [Link do Produto]({item['url']})\n"
            mensagem += " — — — — — — — — —\n"

        await bot.send_message(chat_id, mensagem, parse_mode="MarkdownV2")
    
    else:
        await bot.send_message(chat_id, "Não foi possível listar os produtos")
    

async def get (chat_id, args):

    if not args:
        await bot.send_message(chat_id, "Uso: /get <ID> (Use /list para ver os IDs)")
        return

    product_id = args[0]
    
    historico = get_precos(supabase, product_id)

    if not historico:
        await bot.send_message(chat_id, "Nenhum histórico de preço encontrado")
        return

    mensagem = "📊 *Histórico de Preços*\n\n"

    for item in historico:
        data = item['timestamp'][:10].replace("-", "\/")
        mensagem += f"💰 *R$ {item['preco']:.2f}* \| 📅 {data}\n"

    await bot.send_message(chat_id, mensagem, parse_mode="Markdown")


async def delete (chat_id, id):

    # Somente o Admin pode deletar
    if str(chat_id) != ADMIN_ID:
        await bot.send_message(chat_id, "Você não tem permissão para deletar produtos")
        return

    if not id:
        await bot.send_message(chat_id, "Uso: /delete <ID> (Use /list para listar os IDs)")
        return

    try:
        delete_produto(supabase, id)
        await bot.send_message(chat_id, "Produto deletado com sucesso")
    except Exception as e:
        await bot.send_message(chat_id, "Não foi possível deletar o produto")


# --- Função Principal ---

@app.post("/webhook")
async def run_webhook (request: Request):

    data = await request.json()
    update = Update.de_json(data, bot)
    
    if not update.message or not update.message.text:
        return {"status": "ignored"}

    chat_id = update.message.chat_id

    text_parts = update.message.text.split(" ")
    command = text_parts[0].lower()
    args = text_parts[1:]

    match command:
        case "/start":
            await bot.send_message(chat_id, "Bem-vindo!\n\n Comandos: \n\n `/add`\n `/delete`\n `/list`\n `/get`")
        case "/add":
            await add(chat_id, args)
        case "/delete":
            await delete(chat_id, args)
        case "/list":
            await list(chat_id)
        case "/get":
            await get(chat_id, args)
        case _:
            await bot.send_message(chat_id, "Comando desconhecido.", parse_mode="Markdown")

    return {"status": "ok"}