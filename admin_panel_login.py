# admin_panel_login.py (VERSÃO FINAL COM TODAS AS FERRAMENTAS E TRAVAS DE SEGURANÇA)

import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Optional

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# --- FUNÇÕES DE API ---
def handle_api_error(e: requests.exceptions.RequestException, action: str):
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try: st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except: st.error(f"Detalhe: {e.response.text}")

@st.cache_data(ttl=30)
def get_all_accounts(headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar contas"); return None

def create_new_account(name: str, headers: Dict):
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json={"name": name})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar conta"); return None

@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar usuários"); return None

def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar usuário"); return None

def set_account_status(account_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} conta"); return False

def set_user_status(user_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/users/{user_id}/status?active_status={is_active}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} usuário"); return False

def regenerate_api_key(user_id: int, headers: Dict) -> Optional[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/admin/users/{user_id}/regenerate-api-key", headers=headers)
        response.raise_for_status()
        return response.json().get("api_key")
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "regenerar chave de API"); return None

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'new_api_key_info' not in st.session_state: st.session_state.new_api_key_info = None
if 'confirm_action' not in st.session_state: st.session_state.confirm_action = None

# --- TELA DE LOGIN ---
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    api_key_input = st.text_input("Chave de API de Administrador:", type="password", key="login_api_key")
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
                    else: st.error("Chave de API inválida ou sem permissão de administrador.")
                except requests.exceptions.RequestException: st.error("Não foi possível conectar à API.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.title("Painel de Gestão - SetDoc AI")
headers = {"x-api-key": st.session_state.api_key}

st.sidebar.header("Navegação")
page = st.sidebar.radio("Escolha uma página", ["Gerenciar Contas e Usuários", "Gerenciar Prompts", "Gerenciar Permissões", "Dashboard de Faturamento"])

def logout():
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()
st.sidebar.button("Sair (Logout)", on_click=logout, use_container_width=True)

if st.session_state.new_api_key_info:
    user_name, new_key = st.session_state.new_api_key_info
    st.success(f"Nova API Key gerada para '{user_name}'! Copie e envie ao usuário, ela não será exibida novamente.")
    st.code(new_key)
    st.session_state.new_api_key_info = None

if page == "Gerenciar Contas e Usuários":
    accounts = get_all_accounts(headers)
    if accounts is not None:
        st.header("Visão Geral das Contas")
        df_accounts = pd.DataFrame(accounts)
        st.dataframe(df_accounts[['name', 'is_active', 'id', 'created_at']], hide_index=True, use_container_width=True)

        st.markdown("---")
        st.header("Gerenciamento Detalhado")
        
        account_options = {acc['id']: acc['name'] for acc in accounts}
        selected_account_id = st.selectbox("Selecione uma conta para gerenciar:", options=account_options.keys(), format_func=lambda x: f"{account_options[x]} (ID: {x})")
        
        selected_account = next((acc for acc in accounts if acc['id'] == selected_account_id), None)
        if selected_account:
            st.subheader(f"Ações para a Conta: '{selected_account['name']}'")
            
            is_active = selected_account.get('is_active', True)
            action_label = "Desativar" if is_active else "Reativar"
            action_color = "error" if is_active else "success"
            
            if st.button(f"{action_label} Conta", type=action_color, use_container_width=True):
                st.session_state.confirm_action = ("account_status", selected_account_id, not is_active)
            
            if st.session_state.confirm_action and st.session_state.confirm_action[0] == "account_status" and st.session_state.confirm_action[1] == selected_account_id:
                _, acc_id, new_status = st.session_state.confirm_action
                action_word = "DESATIVAR" if new_status is False else "REATIVAR"
                st.warning(f"**Atenção:** Você tem certeza que deseja {action_word} a conta '{selected_account['name']}'?")
                col1, col2 = st.columns(2)
                if col1.button("Sim, confirmar", use_container_width=True):
                    if set_account_status(acc_id, new_status, headers):
                        st.success("Status da conta atualizado."); st.cache_data.clear()
                        st.session_state.confirm_action = None; st.rerun()
                    else: # A API retornou um erro (ex: usuários ativos)
                        st.session_state.confirm_action = None
                if col2.button("Não, cancelar", use_container_width=True):
                    st.session_state.confirm_action = None; st.rerun()
            
            st.markdown("---")
            st.subheader(f"Usuários da Conta: '{selected_account['name']}'")
            users = get_users_for_account(selected_account_id, headers)
            if users:
                st.dataframe(pd.DataFrame(users)[['full_name', 'email', 'is_active', 'id']], hide_index=True, use_container_width=True)

                user_options = {user['id']: user['full_name'] for user in users}
                selected_user_id = st.selectbox("Selecione um usuário para gerenciar:", options=user_options.keys(), format_func=lambda x: f"{user_options[x]} (ID: {x})")
                
                selected_user = next((user for user in users if user['id'] == selected_user_id), None)
                if selected_user:
                    cols = st.columns(2)
                    is_user_active = selected_user.get('is_active', True)
                    user_action_label = "Desativar" if is_user_active else "Reativar"
                    user_action_color = "error" if is_user_active else "success"

                    with cols[0]:
                        if st.button(f"{user_action_label} Usuário", type=user_action_color, use_container_width=True):
                            st.session_state.confirm_action = ("user_status", selected_user_id, not is_user_active)
                    with cols[1]:
                        if st.button("🔑 Regenerar Chave", use_container_width=True):
                            st.session_state.confirm_action = ("regen_key", selected_user_id)

                    # Lógica de confirmação para ações do usuário
                    if st.session_state.confirm_action and st.session_state.confirm_action[1] == selected_user_id:
                        action_type, user_id = st.session_state.confirm_action[0], st.session_state.confirm_action[1]

                        if action_type == "user_status":
                            new_user_status = st.session_state.confirm_action[2]
                            action_word = "DESATIVAR" if new_user_status is False else "REATIVAR"
                            st.warning(f"**Atenção:** Você tem certeza que deseja {action_word} o usuário '{selected_user['full_name']}'?")
                            col1, col2 = st.columns(2)
                            if col1.button("Sim, confirmar status", use_container_width=True):
                                if set_user_status(user_id, new_user_status, headers):
                                    st.success("Status do usuário atualizado."); st.cache_data.clear()
                                    st.session_state.confirm_action = None; st.rerun()
                            if col2.button("Não, cancelar", use_container_width=True):
                                st.session_state.confirm_action = None; st.rerun()

                        elif action_type == "regen_key":
                            st.warning(f"**Atenção:** Isso invalidará a chave de API antiga do usuário '{selected_user['full_name']}'. Deseja continuar?")
                            col1, col2 = st.columns(2)
                            if col1.button("Sim, regenerar chave", use_container_width=True):
                                new_key = regenerate_api_key(user_id, headers)
                                if new_key:
                                    st.session_state.new_api_key_info = (selected_user['full_name'], new_key)
                                    st.cache_data.clear()
                                    st.session_state.confirm_action = None; st.rerun()
                            if col2.button("Não, cancelar", use_container_width=True):
                                st.session_state.confirm_action = None; st.rerun()

            with st.expander(f"➕ Criar Novo Usuário para '{selected_account['name']}'"):
                with st.form("new_user_form", clear_on_submit=True):
                    full_name = st.text_input("Nome Completo")
                    email = st.text_input("Email")
                    password = st.text_input("Senha", type="password")
                    if st.form_submit_button("Criar Usuário"):
                        if all([full_name, email, password]):
                            response = create_new_user(full_name, email, password, selected_account_id, headers)
                            if response:
                                st.session_state.new_api_key_info = (response['full_name'], response.get('api_key'))
                                st.cache_data.clear(); st.rerun()
                        else: st.warning("Preencha todos os campos.")

        st.markdown("---")
        with st.expander("➕ Criar Nova Conta"):
            with st.form("new_account_form_2", clear_on_submit=True):
                new_account_name = st.text_input("Nome do Novo Cartório")
                if st.form_submit_button("Criar Conta"):
                    if new_account_name:
                        if create_new_account(new_account_name, headers):
                            st.success(f"Conta '{new_account_name}' criada!"); st.cache_data.clear(); st.rerun()
                    else: st.warning("O nome da conta não pode ser vazio.")

elif page == "Gerenciar Prompts":
    st.header("Gerenciar Prompts")
    st.info("Funcionalidade em desenvolvimento.")

elif page == "Gerenciar Permissões":
    st.header("Gerenciar Permissões")
    st.info("Funcionalidade em desenvolvimento.")

elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    st.info("Funcionalidade em desenvolvimento.")
