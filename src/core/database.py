import re
import os
import json
import requests
from supabase import create_client, Client 


# --- Auxiliares ---

def get_supabase_client() -> Client:

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERRO: Chaves do Supabase não configuradas")
        return None
    
    return create_client(url, key)

def envio_alerta (mensagem: str):

    try:
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_ID")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text":mensagem, "parse_mode": "MarkdownV2"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"ERRO: Não foi possível enviar o alerta {e}")

# --- Funções ---

def get_produtos(supabase: Client):

    try:
        resposta = supabase.table("produtos").select("*").order("id").execute()
        return resposta.data
    except Exception as e:
        print(f"ERRO: Não foi possível carregar os produtos {e}")

def get_precos (supabase: Client, product_id: str):

    try:
        resposta = supabase.table("precos").select("*").eq("id_produto", int(product_id)).order("timestamp", desc=True).limit(5).execute()
        return resposta.data
    except Exception as e:
        print(f"ERRO: Não foi possível carregar os preços {e}")

def save_preco (supabase: Client, product_id: str, price: float):

    try:
        data = { "id_produto": product_id, "preco": price}
        supabase.table("precos").insert(data).execute()
        return True
    except Exception as e:
        print(f"ERRO: Não foi possível salvar o preço {e}")
        return False
    
def save_produto (supabase: Client, name: str, url: str):
    
    try:
        data = {"nome": name, "url": url}
        supabase.table("produtos").insert(data).execute()
        return True
    except Exception as e:
        print(f"ERRO: Não foi possível salvar o produto {e}")
        return False
    
def delete_produto (supabase: Client, product_id: str):

    try:

        if isinstance(product_id, list):
            product_id = product_id[0]

        supabase.table("produtos").delete().eq("id", int(product_id)).execute()
        return True
    except Exception as e:
        print(f"ERRO: Não foi possível deletar o produto {e}")
        return False