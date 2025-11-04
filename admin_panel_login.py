# admin_panel_login.py (VERSÃO FINAL COM TELA DE LOGIN)

import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict
from datetime import date

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

# --- FUNÇÕES DE API (COMPLETAS, SEM MUDANÇAS) ---
def handle_api_error(error: requests.exceptions.RequestException, context: str):
    try: detail = error.response.json().get("detail", "Erro desconhecido.")
    except (json.JSONDecodeError, AttributeError): detail = error.response.text
    st.error(f"Erro ao {context}: {detail}")

def get_all_prompts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/prompts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar prompts"); return None
def create_new_prompt(name: str, text: str, headers: Dict):
    try: response = requests.post(f"{API_BASE_URL}/admin/prompts/", headers=headers, json={"name": name, "prompt_text": text}); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar prompt"); return None
# ... (todas as outras funções de API permanecem aqui, omitidas para brevidade) ...
def get_all_accounts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None
def get_billing_report(account_id: int, start_date: str, end_date: str, headers: Dict):
    params = {"account_id": account_id, "start_date": start_date, "end_date": end_date}
    try: response = requests.get(f"{API_BASE_URL}/billing/report/", headers=headers, params=params); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório resumido"); return None
def get_detailed_billing_report(account_id: int, start_date: str, end_date: str, headers: Dict):
    params = {"account_id": account_id, "start_date": start_date, "end_date": end_date}
    try: response = requests.get(f"{API_BASE_URL}/billing/report/detailed", headers=headers, params=params); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório detalhado"); return None

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""

# --- INTERFACE ---
st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# ==============================================================================
# TELA DE LOGIN
# Esta parte só é mostrada se o usuário NÃO estiver autenticado.
# ==============================================================================
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    st.markdown("---")
    
    api_key_input = st.text_input(
        "Por favor, insira sua Chave de API de Administrador para continuar:",
        type="password",
        key="login_api_key"
    )

    if st.button("Entrar", use_container_width=True):
        if not api_key_input:
            st.warning("O campo da chave de API não pode estar vazio.")
        else:
            # Tenta validar a chave fazendo uma chamada leve à API
            with st.spinner("Validando chave..."):
                test_headers = {"x-api-key": api_key_input}
                try:
                    response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=test_headers, timeout=10)
                    if response.status_code == 200:
                        st.session_state.is_authenticated = True
                        st.session_state.api_key = api_key_input
                        st.rerun() # Recarrega a página para mostrar o painel principal
                    else:
                        st.error("Chave de API inválida ou sem permissão. Verifique a chave e tente novamente.")
                except requests.exceptions.RequestException:
                    st.error("Não foi possível conectar à API para validar a chave. Verifique sua conexão.")
    
    # Impede a execução do resto do script se não estiver logado
    st.stop()

# ==============================================================================
# PAINEL PRINCIPAL
# Esta parte só é executada se o usuário ESTIVER autenticado.
# ==============================================================================

st.title("Painel de Gestão - SetDoc AI")

# Define os headers para todas as chamadas de API da sessão
headers = {"x-api-key": st.session_state.api_key}

st.sidebar.header("Navegação")
page = st.sidebar.radio("Escolha uma página", ["Gerenciar Prompts", "Gerenciar Permissões", "Gerenciar Contas e Usuários", "Dashboard de Faturamento"])

# Botão de Logout
def logout():
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""
st.sidebar.button("Sair (Logout)", on_click=logout)


# O resto do código das páginas permanece o mesmo...
if page == "Gerenciar Prompts":
    st.header("Gerenciar Catálogo de Prompts")
    # ... (código da página de prompts) ...
    pass

elif page == "Gerenciar Permissões":
    st.header("Gerenciar Permissões por Cartório")
    # ... (código da página de permissões) ...
    pass

elif page == "Gerenciar Contas e Usuários":
    st.header("Gerenciar Contas (Cartórios) e Usuários")
    # ... (código da página de contas) ...
    pass

elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    accounts = get_all_accounts(headers)
    if accounts is not None:
        if not accounts:
            st.info("Nenhum cartório cadastrado.")
        else:
            # ... (todo o resto do código da página de faturamento) ...
            pass