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
        await bot.send_message(chat_id, "<b>Uso:</b> <code>/add &lt;URL&gt;</code>", parse_mode="HTML")
        return

    # Somente o Admin pode adicionar
    if str(chat_id) != ADMIN_ID:
        await bot.send_message(chat_id, "❌ <b>Acesso Negado:</b> Você não tem permissão para adicionar produtos", parse_mode="HTML")
        return
    
    url = args[0]
    dominio = urlparse(url).netloc

    if dominio not in STORE_CONFIG:
        await bot.send_message(chat_id, f"⚠️ <b>Erro:</b> O site <i>{dominio}</i> não está configurado no sistema", parse_mode="HTML")
        return 
    
    product_info = scrape_product(url, STORE_CONFIG[dominio])

    if product_info and  product_info['title'] != "Título não encontrado":
        save_produto(supabase, product_info['title'], url)
        await bot.send_message(chat_id, f"✅ <b>Produto Adicionado:</b>\n{product_info['title']}", parse_mode="HTML")
    else:
        await bot.send_message(chat_id, "⚠️ <b>Erro:</b> Não foi possível adicionar o produto", parse_mode="HTML")


async def list (chat_id):
    
    produtos = get_produtos(supabase)

    if produtos:

        if not produtos:
            await bot.send_message(chat_id, "Nenhum produto encontrado")
            return

        mensagem = "<b>📋 Produtos Monitorados</b>\n\n"
        mensagem += "————————————————\n"

        for item in produtos:
            mensagem += f"🆔 ID: <code>{item['id']}</code>\n"
            mensagem += f"📦 <b>{item['nome']}</b>\n\n"
            mensagem += f"🔗 <a href='{item['url']}'>Ver na Loja</a>\n"
            mensagem += "————————————————\n"

        await bot.send_message(chat_id, mensagem, parse_mode="HTML")
    
    else:
        await bot.send_message(chat_id, "⚠️ <b>Erro:</b> Não foi possível listar os produtos", parse_mode="HTML")
    

async def get (chat_id, args):

    if not args:
        await bot.send_message(chat_id, "<b>Uso:</b> <code>/get &lt;ID&gt;</code>\n<i>(Use /list para ver os IDs)</i>", parse_mode="HTML")
        return

    product_id = args[0]
    
    historico = get_precos(supabase, product_id)

    if not historico:
        await bot.send_message(chat_id, f"<b>Histórico vazio:</b> Não encontrei preços para esse produto", parse_mode="HTML")
        return

    mensagem = "📊 *Histórico de Preços*\n\n"

    for item in historico:
        data = item['timestamp'][:10].replace("-", "/")
        mensagem += f"💰 <b>R$ {item['preco']:.2f}</b> | 📅 {data}\n"

    await bot.send_message(chat_id, mensagem, parse_mode="HTML")


async def delete (chat_id, id):

    # Somente o Admin pode deletar
    if str(chat_id) != ADMIN_ID:
        await bot.send_message(chat_id, "❌ <b>Acesso Negado:</b> Você não tem permissão para deletar produtos", parse_mode="HTML")
        return

    if not id:
        await bot.send_message(chat_id, "<b>Uso:</b> <code>/delete &lt;ID&gt;</code>", parse_mode="HTML")
        return

    try:
        delete_produto(supabase, id)
        await bot.send_message(chat_id, f"🗑️ <b>Sucesso:</b> Produto <code>{id}</code> foi removido.", parse_mode="HTML")
    except Exception as e:
        await bot.send_message(chat_id, f"⚠️ <b>Erro:</b> Não foi possível deletar o produto", parse_mode="HTML")


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
            mensagem = (
                f"Comandos Disponíveis:\n\n"
                f"<code>/add &lt;link&gt;</code> - Monitorar novo item\n"
                f"<code>/list</code> - Ver todos os produtos\n"
                f"<code>/get &lt;id&gt;</code> - Ver histórico de preço\n"
                f"<code>/delete &lt;id&gt;</code> - Parar monitoramento de um item"
            )
            await bot.send_message(chat_id, mensagem, parse_mode="HTML")
        case "/add":
            await add(chat_id, args)
        case "/delete":
            await delete(chat_id, args)
        case "/list":
            await list(chat_id)
        case "/get":
            await get(chat_id, args)
        case _:
            await bot.send_message(chat_id, "Comando desconhecido.\nDigite <code>/start</code> para ver as opções", parse_mode="HTML")

    return {"status": "ok"}