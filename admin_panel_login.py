# admin_panel_login.py (VERSÃO FINAL COM TODAS AS FERRAMENTAS DE GESTÃO)

import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Optional

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# --- FUNÇÕES DE API (COM CACHE PARA MELHORAR PERFORMANCE) ---

def handle_api_error(e: requests.exceptions.RequestException, action: str):
    """Função centralizada para lidar com erros de API."""
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try:
            st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except:
            st.error(f"Detalhe: {e.response.text}")

@st.cache_data(ttl=30)
def get_all_accounts(headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar contas")
        return None

def create_new_account(name: str, headers: Dict, **kwargs):
    payload = {"name": name, **kwargs}
    payload_clean = {k: v for k, v in payload.items() if v is not None and v != ""}
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json=payload_clean)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar conta")
        return None

@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar usuários")
        return None

def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar usuário")
        return None

# --- NOVAS FUNÇÕES DE API PARA GESTÃO ---

def set_account_status(account_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} conta")
        return False

def set_user_status(user_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/users/{user_id}/status?active_status={is_active}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} usuário")
        return False

def regenerate_api_key(user_id: int, headers: Dict) -> Optional[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/admin/users/{user_id}/regenerate-api-key", headers=headers)
        response.raise_for_status()
        return response.json().get("api_key")
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "regenerar chave de API")
        return None

# --- O restante das funções (prompts, permissions, billing) pode ser adicionado aqui se necessário ---

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""
if 'new_api_key' not in st.session_state:
    st.session_state.new_api_key = None

# --- TELA DE LOGIN ---
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    api_key_input = st.text_input("Chave de API de Administrador:", type="password", key="login_api_key")
    if st.button("Entrar", use_container_width=True):
        if not api_key_input:
            st.warning("O campo da chave de API não pode estar vazio.")
        else:
            with st.spinner("Validando chave..."):
                try:
                    # Testamos o acesso tentando buscar as contas, que é um endpoint de admin
                    response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers={"x-api-key": api_key_input}, timeout=10)
                    if response.status_code == 200:
                        st.session_state.is_authenticated = True
                        st.session_state.api_key = api_key_input
                        st.rerun()
                    else:
                        st.error("Chave de API inválida ou sem permissão de administrador.")
                except requests.exceptions.RequestException:
                    st.error("Não foi possível conectar à API para validar a chave.")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.title("Painel de Gestão - SetDoc AI")
headers = {"x-api-key": st.session_state.api_key}

st.sidebar.header("Navegação")
# Removi as páginas não implementadas para focar na gestão de contas/usuários
page = st.sidebar.radio("Escolha uma página", ["Gerenciar Contas e Usuários"])

def logout():
    # Limpa todo o estado da sessão
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

st.sidebar.button("Sair (Logout)", on_click=logout, use_container_width=True)

# --- Exibir a nova API Key gerada (se houver) ---
if st.session_state.new_api_key:
    st.success("Nova API Key gerada com sucesso! Copie e envie ao usuário, ela não será exibida novamente.")
    st.code(st.session_state.new_api_key)
    st.session_state.new_api_key = None # Limpa após exibir

if page == "Gerenciar Contas e Usuários":
    st.header("Gerenciar Contas (Cartórios)")
    
    accounts = get_all_accounts(headers)
    if accounts is not None:
        # Adiciona a coluna de ações dinamicamente
        for acc in accounts:
            acc['status'] = "Ativa" if acc.get('is_active', True) else "Inativa"
        
        df_accounts = pd.DataFrame(accounts)
        cols_to_show = ['name', 'status', 'is_active', 'id', 'created_at']
        df_accounts_display = df_accounts.reindex(columns=cols_to_show)
        
        st.dataframe(df_accounts_display, hide_index=True, use_container_width=True,
                     column_config={"is_active": None}) # Oculta a coluna booleana crua

        st.subheader("Ações nas Contas")
        if accounts:
            selected_account_id_action = st.selectbox("Selecione uma conta para gerenciar",
                                                     options=[acc['id'] for acc in accounts],
                                                     format_func=lambda x: f"{next(acc['name'] for acc in accounts if acc['id'] == x)} (ID: {x})")
            
            selected_account = next((acc for acc in accounts if acc['id'] == selected_account_id_action), None)
            
            if selected_account:
                col1, col2 = st.columns(2)
                is_active = selected_account.get('is_active', True)
                
                with col1:
                    if is_active:
                        if st.button("🔴 Desativar Conta", key=f"deact_acc_{selected_account_id_action}", use_container_width=True):
                            if set_account_status(selected_account_id_action, False, headers):
                                st.success(f"Conta '{selected_account['name']}' desativada.")
                                st.cache_data.clear(); st.rerun()
                    else:
                        if st.button("🟢 Reativar Conta", key=f"act_acc_{selected_account_id_action}", use_container_width=True):
                            if set_account_status(selected_account_id_action, True, headers):
                                st.success(f"Conta '{selected_account['name']}' reativada.")
                                st.cache_data.clear(); st.rerun()

        with st.expander("➕ Criar Nova Conta de Cartório"):
            with st.form("new_account_form", clear_on_submit=True):
                new_account_name = st.text_input("Nome do Novo Cartório")
                if st.form_submit_button("Criar Conta"):
                    if new_account_name:
                        if create_new_account(new_account_name, headers):
                            st.success(f"Conta '{new_account_name}' criada!"); st.cache_data.clear(); st.rerun()
                    else:
                        st.warning("O nome da conta não pode ser vazio.")
        
        st.markdown("---")
        st.header("Gerenciar Usuários")
        
        if accounts:
            account_options = {acc['id']: acc['name'] for acc in accounts}
            selected_account_id_users = st.selectbox("Selecione a Conta para ver/adicionar usuários:",
                                                     options=sorted(account_options.keys()),
                                                     format_func=lambda x: account_options[x])
            
            if selected_account_id_users:
                users = get_users_for_account(selected_account_id_users, headers)
                if users is not None:
                    st.write(f"**Usuários em '{account_options[selected_account_id_users]}':**")
                    if users:
                        for user in users:
                            user_id = user['id']
                            is_user_active = user.get('is_active', True)
                            
                            cols = st.columns([2, 1, 1, 1])
                            cols[0].dataframe(pd.DataFrame([user]), hide_index=True, use_container_width=True)
                            
                            with cols[1]:
                                if is_user_active:
                                    if st.button("🔴 Desativar", key=f"deact_usr_{user_id}", use_container_width=True):
                                        if set_user_status(user_id, False, headers):
                                            st.success("Usuário desativado."); st.cache_data.clear(); st.rerun()
                                else:
                                    if st.button("🟢 Reativar", key=f"act_usr_{user_id}", use_container_width=True):
                                        if set_user_status(user_id, True, headers):
                                            st.success("Usuário reativado."); st.cache_data.clear(); st.rerun()
                            with cols[2]:
                                if st.button("🔑 Regenerar Chave", key=f"regen_key_{user_id}", use_container_width=True):
                                    with st.spinner("Gerando nova chave..."):
                                        new_key = regenerate_api_key(user_id, headers)
                                        if new_key:
                                            st.session_state.new_api_key = new_key
                                            st.cache_data.clear()
                                            st.rerun()
                    else:
                        st.info("Nenhum usuário nesta conta.")

                with st.expander(f"➕ Criar Novo Usuário para '{account_options[selected_account_id_users]}'"):
                    with st.form("new_user_form"):
                        full_name = st.text_input("Nome Completo do Usuário")
                        email = st.text_input("Email")
                        password = st.text_input("Senha", type="password")
                        
                        if st.form_submit_button("Criar Usuário"):
                            if all([full_name, email, password]):
                                with st.spinner("Criando usuário..."):
                                    response = create_new_user(full_name, email, password, selected_account_id_users, headers)
                                    if response:
                                        st.session_state.new_api_key = response.get('api_key')
                                        st.cache_data.clear()
                                        st.rerun()
                            else: 
                                st.warning("Preencha os campos de Nome, Email e Senha.")
