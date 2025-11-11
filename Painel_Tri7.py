# admin_panel_main.py (PONTO DE ENTRADA E AUTENTICAÇÃO)

import streamlit as st
import sys
import os

# Adiciona o caminho da raiz do projeto para que as páginas consigam importar o módulo de funções
sys.path.insert(0, os.path.dirname(__file__))

from shared_funcs import check_admin_auth

st.set_page_config(layout="wide", page_title="Painel de Gestão Tri7 AI")

# --- INICIALIZAÇÃO DA SESSÃO ---
st.session_state.setdefault('is_authenticated', False)
st.session_state.setdefault('api_key', "")
st.session_state.setdefault('new_api_key_info', None)
st.session_state.setdefault('confirm_action', None)
st.session_state.setdefault('last_perm_account_id', None) 
st.session_state.setdefault('billing_report_data', None)

# --- TELA DE LOGIN / PROTEÇÃO ---
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - Tri7 AI")
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
st.title("Painel de Gestão - Tri7 AI")

def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.sidebar.title("Navegação")
st.sidebar.button("Sair (Logout)", on_click=logout, use_container_width=True)

st.sidebar.header("Módulos")
st.markdown("Selecione um módulo na barra lateral para começar.")



