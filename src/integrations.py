import os
import json
import re
import gspread

# --- Funções Auxiliares ---

# Limpa o nome de um produto para ser um nome de guia válido
def clear_name(name):

    name = re.sub(r'[\\/*?:\[\]]', '', name)
    return name[:40] # Trunca para 40 caracteres

# --- Google Sheets ---

def get_sheets_client():
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json_str:
        print("  - ERRO: Secret GOOGLE_CREDENTIALS não encontrado.")
        return None
    creds_dict = json.loads(creds_json_str)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    return gspread.service_account_from_dict(creds_dict, scopes=scope)

# Carrega a lista de produtos do Sheets
def load_products(gc):
    try:
        spreadsheet = gc.open("Historico Precos")
        worksheet = spreadsheet.worksheet("Produtos")
        urls = worksheet.col_values(1)[1:]
        print(f"  - {len(urls)} URL(s) encontradas na planilha.")
        return urls
    except Exception as e:
        print(f"  - ERRO ao ler as URLs da planilha: {e}")
    return []

# Salva os dados na planilha
def save_product_data(spreadsheet, product_data, timestamp):
    try:
        sheet_name = clear_name(product_data['title'])

        try:
            product_sheet = spreadsheet.worksheet(sheet_name) # Tenta encontrar a guia do produto
        except gspread.exceptions.WorksheetNotFound:
            print(f"  - Criando nova guia para o produto: '{sheet_name}'") 
            product_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="20") # Se não encontrar, cria a guia
            product_sheet.append_row(['Timestamp', 'Preco'])

        # Adiciona a nova linha pesquisada
        product_sheet.append_row([timestamp, product_data['price']])

    except Exception as e:
        print(f"  - ERRO AO SALVAR DADOS: {e}")