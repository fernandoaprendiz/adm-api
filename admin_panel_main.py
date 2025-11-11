# admin_panel_main.py (PONTO DE ENTRADA E AUTENTICAÇÃO)

import streamlit as st
import requests
from typing import Dict

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# --- FUNÇÕES DE API SIMPLIFICADAS PARA AUTENTICAÇÃO ---
def handle_api_error(e: requests.exceptions.RequestException, action: str):
    """Função centralizada para lidar com erros de API."""
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try: st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except: st.error(f"Detalhe: {e.response.text}")

def check_admin_auth(api_key: str) -> bool:
    """Tenta autenticar no endpoint de admin."""
    headers = {"x-api-key": api_key}
    try:
        # Tenta acessar um endpoint de admin protegido (ex: listar contas)
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 403:
            return False # Sem permissão
        handle_api_error(e, "conectar e validar chave")
        return False

# --- INICIALIZAÇÃO DA SESSÃO ---
st.session_state.setdefault('is_authenticated', False)
st.session_state.setdefault('api_key', "")
# Inicializa o estado para as novas funcionalidades (mantenha-o aqui)
st.session_state.setdefault('new_api_key_info', None)
st.session_state.setdefault('confirm_action', None)
st.session_state.setdefault('last_perm_account_id', None) 
st.session_state.setdefault('billing_report_data', None)

# --- TELA DE LOGIN / PROTEÇÃO ---
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    api_key_input = st.text_input("Chave de API de Administrador:", type="password", key="login_api_key")
    if st.button("Entrar", use_container_width=True):
        if check_admin_auth(api_key_input):
            st.session_state.is_authenticated = True
            st.session_state.api_key = api_key_input
            st.rerun()
        else:
            st.error("Chave de API inválida ou sem permissão de administrador.")
    st.stop()

# --- FUNÇÕES DE NAVEGAÇÃO / LOGOUT (Exibidas após o Login) ---
st.title("Painel de Gestão - SetDoc AI")

def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.sidebar.title("Navegação")
st.sidebar.button("Sair (Logout)", on_click=logout, use_container_width=True)

st.sidebar.header("Módulos")
st.markdown("Selecione um módulo na barra lateral para começar.")