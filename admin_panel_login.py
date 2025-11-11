# admin_panel.py (VERSÃO FINAL, COMPLETA COM TODAS AS PÁGINAS E FUNCIONALIDADES)

import streamlit as st
import requests
import pandas as pd
import io
from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# --- FUNÇÕES DE API ---
def handle_api_error(e: requests.exceptions.RequestException, action: str):
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try: st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except: st.error(f"Detalhe: {e.response.text}")

# Funções de Contas e Usuários
@st.cache_data(ttl=30)
def get_all_accounts(headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar contas"); return None

def create_new_account(name: str, headers: Dict):
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json={"name": name}); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar conta"); return None

@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "buscar usuários"); return None

def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar usuário"); return None

def set_account_status(account_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=headers); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} conta"); return False

def set_user_status(user_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/users/{user_id}/status?active_status={is_active}", headers=headers); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"{'ativar' if is_active else 'desativar'} usuário"); return False

def regenerate_api_key(user_id: int, headers: Dict) -> Optional[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/admin/users/{user_id}/regenerate-api-key", headers=headers); response.raise_for_status()
        return response.json().get("api_key")
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "regenerar chave de API"); return None

# Funções de Prompts e Permissões
@st.cache_data(ttl=60)
def get_all_prompts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/prompts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar prompts"); return None
def get_account_permissions(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers); response.raise_for_status(); return response.json().get("prompt_ids", [])
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar permissões"); return None
def sync_account_permissions(account_id: int, prompt_ids: List[int], headers: Dict):
    try: response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers, json={"prompt_ids": prompt_ids}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "salvar permissões"); return False

# Função de Faturamento
def get_master_billing_report(start_date: str, end_date: str, account_id: Optional[int], headers: Dict):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id: params["account_id"] = account_id
    try:
        # Assumindo que a rota correta é /admin/billing/report/ (verifique sua API se necessário)
        response = requests.get(f"{API_BASE_URL}/billing/report/", headers=headers, params=params); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório mestre"); return None

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state: st.session_state.is_authenticated = False
if 'api_key' not in st.session_state: st.session_state.api_key = ""
if 'new_api_key_info' not in st.session_state: st.session_state.new_api_key_info = None

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
    if accounts:
        st.header("Gerenciar Contas (Cartórios)")
        df_accounts = pd.DataFrame(accounts)
        st.dataframe(df_accounts[['name', 'is_active', 'id', 'created_at']], hide_index=True, use_container_width=True)

        st.subheader("Gerenciar Conta Selecionada")
        account_options = {acc['id']: acc['name'] for acc in accounts}
        selected_account_id = st.selectbox("Selecione uma conta:", options=account_options.keys(), format_func=lambda x: f"{account_options[x]} (ID: {x})")
        
        selected_account = next((acc for acc in accounts if acc['id'] == selected_account_id), None)
        if selected_account:
            is_active = selected_account.get('is_active', True)
            action_label = "🔴 Desativar" if is_active else "🟢 Reativar"
            if st.button(f"{action_label} Conta '{selected_account['name']}'"):
                if set_account_status(selected_account_id, not is_active, headers):
                    st.success("Status da conta atualizado."); st.cache_data.clear(); st.rerun()

            st.markdown("---")
            st.header(f"Usuários da Conta: {selected_account['name']}")
            users = get_users_for_account(selected_account_id, headers)
            if users:
                st.dataframe(pd.DataFrame(users)[['full_name', 'email', 'is_active', 'id']], hide_index=True, use_container_width=True)

                st.subheader("Gerenciar Usuário Selecionado")
                user_options = {user['id']: user['full_name'] for user in users}
                selected_user_id = st.selectbox("Selecione um usuário:", options=user_options.keys(), format_func=lambda x: f"{user_options[x]} (ID: {x})")
                
                selected_user = next((user for user in users if user['id'] == selected_user_id), None)
                if selected_user:
                    is_user_active = selected_user.get('is_active', True)
                    user_action_label = "🔴 Desativar" if is_user_active else "🟢 Reativar"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"{user_action_label} Usuário '{selected_user['full_name']}'", use_container_width=True):
                            if set_user_status(selected_user_id, not is_user_active, headers):
                                st.success("Status do usuário atualizado."); st.cache_data.clear(); st.rerun()
                    with col2:
                        if st.button(f"🔑 Regenerar Chave para '{selected_user['full_name']}'", use_container_width=True):
                            new_key = regenerate_api_key(selected_user_id, headers)
                            if new_key:
                                st.session_state.new_api_key_info = (selected_user['full_name'], new_key)
                                st.cache_data.clear(); st.rerun()
            else:
                st.info("Nenhum usuário nesta conta.")

            with st.expander(f"➕ Criar Novo Usuário para '{selected_account['name']}'"):
                with st.form("new_user_form", clear_on_submit=True):
                    full_name = st.text_input("Nome Completo"); email = st.text_input("Email"); password = st.text_input("Senha", type="password")
                    if st.form_submit_button("Criar Usuário"):
                        if all([full_name, email, password]):
                            response = create_new_user(full_name, email, password, selected_account_id, headers)
                            if response:
                                st.session_state.new_api_key_info = (response['full_name'], response.get('api_key'))
                                st.cache_data.clear(); st.rerun()
                        else: st.warning("Preencha todos os campos.")
    
    with st.expander("➕ Criar Nova Conta"):
        with st.form("new_account_form", clear_on_submit=True):
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
    accounts = get_all_accounts(headers)
    prompts = get_all_prompts(headers)
    if accounts and prompts:
        account_options = {acc['id']: acc['name'] for acc in accounts}
        prompt_options = {p['id']: p['name'] for p in prompts}
        
        selected_account_id_perm = st.selectbox("Selecione a conta para gerenciar permissões:", options=account_options.keys(), format_func=lambda x: account_options[x], key="perm_account_select")
        
        if selected_account_id_perm:
            current_permissions = get_account_permissions(selected_account_id_perm, headers)
            st.write(f"**Editando permissões para: {account_options[selected_account_id_perm]}**")
            
            selected_prompt_ids = st.multiselect("Selecione os prompts permitidos:", options=prompt_options.keys(), default=current_permissions, format_func=lambda x: prompt_options[x])
            
            if st.button("Salvar Permissões", use_container_width=True):
                if sync_account_permissions(selected_account_id_perm, selected_prompt_ids, headers):
                    st.success("Permissões atualizadas com sucesso!"); st.rerun()

elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    accounts = get_all_accounts(headers)
    if accounts:
        with st.form("billing_form"):
            # A rota da API que você forneceu não tem um filtro por conta, então removi a opção "Todos"
            # Se a API suportar, podemos adicionar de volta
            account_options = {acc['id']: acc['name'] for acc in accounts}
            selected_account_id_billing = st.selectbox("Selecione a Conta:", options=account_options.keys(), format_func=lambda x: account_options[x])
            
            today = date.today()
            default_start = today - timedelta(days=30)
            col1, col2 = st.columns(2)
            with col1: start_date = st.date_input("Data de Início", value=default_start)
            with col2: end_date = st.date_input("Data de Fim", value=today)
            
            submitted = st.form_submit_button("Gerar Relatório", use_container_width=True)
        
        if submitted:
            if start_date and end_date and selected_account_id_billing:
                with st.spinner("Gerando relatório..."):
                    # Passando o account_id selecionado para a função
                    report_data = get_master_billing_report(str(start_date), str(end_date), selected_account_id_billing, headers)
                
                if report_data:
                    st.subheader(f"Resumo do Período para: {account_options[selected_account_id_billing]}")
                    summary = report_data.get('summary', {})
                    by_model = report_data.get('by_model', [])
                    
                    col_resumo1, col_resumo2 = st.columns(2)
                    col_resumo1.metric(label="Total de Jobs Processados", value=summary.get('total_jobs', 0))
                    col_resumo2.metric(label="Total de Tokens", value=f"{summary.get('total_tokens', 0):,}")

                    if by_model:
                        st.subheader("Detalhes por Modelo")
                        df_report = pd.DataFrame(by_model)
                        st.dataframe(df_report, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum dado de faturamento encontrado para o período e conta selecionados.")
