import os
import json
import re
from supabase import create_client, Client 


# --- Supabase ---

def get_supabase_client() -> Client:

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERRO: Chaves do Supabase não configuradas")
        return None
    
    return create_client(url, key)

def get_produtos(supabase: Client):

    try:
        resposta = supabase.table("produtos").select("id, url").execute()
        return resposta.data
    except Exception as e:
        print(f"ERRO: Não foi possível carregar os produtos {e}")

def get_precos (supabase: Client, product_id: str):

    try:
        resposta = supabase.table("precos").select("*").eq("id_produto", product_id).execute()
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
        supabase.table("produtos").delete().eq("id", product_id).execute()
    except Exception as e:
        print(f"ERRO: Não foi possível deletar o produto {e}")
        return None