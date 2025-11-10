# admin_panel_login.py (VERSÃO FINAL, COM CORREÇÃO DEFINITIVA NA EXIBIÇÃO DA API KEY)

import streamlit as st
import requests
import json
import pandas as pd
import io
from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

# st.set_page_config DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT
st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# --- FUNÇÕES DE API (COM CACHE PARA MELHORAR PERFORMANCE) ---
@st.cache_data(ttl=60)
def get_all_prompts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/prompts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar prompts"); return None
def create_new_prompt(name: str, text: str, headers: Dict):
    try: response = requests.post(f"{API_BASE_URL}/admin/prompts/", headers=headers, json={"name": name, "prompt_text": text}); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar prompt"); return None
def update_prompt(prompt_id: int, name: str, text: str, headers: Dict):
    try: response = requests.put(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=headers, json={"name": name, "prompt_text": text}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "atualizar prompt"); return False
def delete_prompt(prompt_id: int, headers: Dict):
    try: response = requests.delete(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=headers); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "deletar prompt"); return False
@st.cache_data(ttl=60)
def get_all_accounts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None
def get_account_permissions(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers); response.raise_for_status(); return response.json().get("prompt_ids", [])
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar permissões"); return None
def sync_account_permissions(account_id: int, prompt_ids: List[int], headers: Dict):
    try: response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers, json={"prompt_ids": prompt_ids}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "salvar permissões"); return False
def create_new_account(name: str, headers: Dict, cod_tri7: Optional[int], cidade: Optional[str], uf: Optional[str]):
    payload = {"name": name, "cod_tri7": cod_tri7, "cidade": cidade, "uf": uf}
    payload_clean = {k: v for k, v in payload.items() if v is not None and v != ""}
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json=payload_clean); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar conta"); return None
def get_users_for_account(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None
def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar usuário"); return None
def get_master_billing_report(start_date: str, end_date: str, account_id: Optional[int], headers: Dict):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id: params["account_id"] = account_id
    try:
        response = requests.get(f"{API_BASE_URL}/admin/billing/master-report", headers=headers, params=params); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório mestre"); return None

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""

# --- TELA DE LOGIN ---
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    st.markdown("---")
    api_key_input = st.text_input("Chave de API de Administrador:", type="password")
    if st.button("Entrar", use_container_width=True):
        if not api_key_input: st.warning("O campo da chave de API não pode estar vazio.")
        else:
            with st.spinner("Validando chave..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers={"x-api-key": api_key_input}, timeout=10)
                    if response.status_code == 200:
                        st.session_state.is_authenticated = True
                        st.session_state.api_key = api_key_input
                        st.rerun()
                    else: st.error("Chave de API inválida ou sem permissão.")
                except requests.exceptions.RequestException: st.error("Não foi possível conectar à API para validar a chave.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.title("Painel de Gestão - SetDoc AI")
headers = {"x-api-key": st.session_state.api_key}

st.sidebar.header("Navegação")
page = st.sidebar.radio("Escolha uma página", ["Gerenciar Contas e Usuários", "Gerenciar Prompts", "Gerenciar Permissões", "Dashboard de Faturamento"])

def logout():
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""
st.sidebar.button("Sair (Logout)", on_click=logout)

if page == "Gerenciar Contas e Usuários":
    st.header("Gerenciar Contas (Cartórios) e Usuários")
    accounts = get_all_accounts(headers)
    if accounts is not None:
        st.subheader("Contas de Cartório Existentes")
        df_accounts = pd.DataFrame(accounts)
        cols_to_show = ['name', 'cod_tri7', 'cidade', 'uf', 'id', 'created_at']
        df_accounts_display = df_accounts.reindex(columns=cols_to_show)
        st.dataframe(df_accounts_display, hide_index=True, use_container_width=True)
        
        with st.expander("Criar Nova Conta de Cartório"):
            with st.form("new_account_form", clear_on_submit=True):
                new_account_name = st.text_input("Nome do Novo Cartório")
                st.markdown("###### Informações de Localização (Opcional)")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1: cod_tri7 = st.number_input("Código TRI7", step=1, value=None, placeholder="Apenas números")
                with col2: cidade = st.text_input("Cidade")
                with col3: uf = st.text_input("UF", max_chars=2)
                if st.form_submit_button("Criar Conta"):
                    if new_account_name:
                        if create_new_account(new_account_name, headers, cod_tri7=cod_tri7, cidade=cidade, uf=uf.upper() if uf else None):
                            st.success(f"Conta '{new_account_name}' criada!"); st.rerun()
                    else: st.warning("O nome da conta não pode ser vazio.")
        
        st.markdown("---")
        st.subheader("Gerenciar Usuários")
        account_options = {acc['name']: acc['id'] for acc in accounts}
        selected_account_name = st.selectbox("Selecione a Conta para ver/adicionar usuários:", options=sorted(account_options.keys()))
        if selected_account_name:
            selected_account_id = account_options[selected_account_name]
            users = get_users_for_account(selected_account_id, headers)
            if users is not None:
                st.write(f"**Usuários em '{selected_account_name}':**")
                if users:
                    st.dataframe(pd.DataFrame(users), hide_index=True)
                else:
                    st.info("Nenhum usuário nesta conta.")
            with st.expander(f"Criar Novo Usuário para '{selected_account_name}'"):
                # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
                with st.form("new_user_form", clear_on_submit=False):
                    full_name = st.text_input("Nome Completo do Usuário")
                    email = st.text_input("Email")
                    password = st.text_input("Senha", type="password")
                    
                    if st.form_submit_button("Criar Usuário"):
                        if all([full_name, email, password]):
                            with st.spinner("Criando usuário..."):
                                response = create_new_user(full_name, email, password, selected_account_id, headers)
                                if response:
                                    st.success(f"Usuário '{response['full_name']}' criado com sucesso!")
                                    st.info("API Key gerada (copie e envie ao usuário, ela não será exibida novamente):")
                                    st.code(response['api_key'])
                        else: 
                            st.warning("Preencha os campos de Nome, Email e Senha.")
                            
elif page == "Gerenciar Prompts":
    # ... (código existente, sem alterações)
    pass
elif page == "Gerenciar Permissões":
    # ... (código existente, sem alterações)
    pass
elif page == "Dashboard de Faturamento":
    # ... (código existente, sem alterações)
    pass
