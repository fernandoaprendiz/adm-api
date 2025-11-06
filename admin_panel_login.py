# admin_panel_login.py (VERSÃO CORRIGIDA - Lógica de Localização na Conta)

import streamlit as st
import requests
import json
import pandas as pd
from typing import List, Dict, Optional
from datetime import date, timedelta

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

# --- FUNÇÃO DE AJUDA PARA TRATAR ERROS DE API ---
def handle_api_error(error: requests.exceptions.RequestException, context: str):
    try:
        detail = error.response.json().get("detail", "Erro desconhecido.")
    except (json.JSONDecodeError, AttributeError):
        detail = error.response.text
    st.error(f"Erro ao {context}: {detail}")

# --- FUNÇÕES DE API ---
# (Funções não relacionadas a Conta/Usuário permanecem iguais)
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
def get_all_accounts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None
def get_account_permissions(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers); response.raise_for_status(); return response.json().get("prompt_ids", [])
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar permissões"); return None
def sync_account_permissions(account_id: int, prompt_ids: List[int], headers: Dict):
    try: response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers, json={"prompt_ids": prompt_ids}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "salvar permissões"); return False

# ▼▼▼ 1. ATUALIZAR A FUNÇÃO `create_new_account` PARA ACEITAR OS NOVOS PARÂMETROS ▼▼▼
def create_new_account(
    name: str, 
    headers: Dict,
    cod_tri7: Optional[int],
    cidade: Optional[str],
    uf: Optional[str]
):
    payload = {
        "name": name,
        "cod_tri7": cod_tri7,
        "cidade": cidade,
        "uf": uf
    }
    # Remove chaves com valores nulos ou vazios para não enviar para a API
    payload_clean = {k: v for k, v in payload.items() if v is not None and v != ""}
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json=payload_clean)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "criar conta")
        return None

def get_users_for_account(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None

# ▼▼▼ 2. SIMPLIFICAR A FUNÇÃO `create_new_user` (REMOVER CAMPOS DE LOCALIZAÇÃO) ▼▼▼
def create_new_user(
    full_name: str, 
    email: str, 
    password: str, 
    account_id: int, 
    headers: Dict
):
    payload = {
        "full_name": full_name, 
        "email": email, 
        "password": password, 
        "account_id": account_id
    }
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: 
        handle_api_error(e, "criar usuário")
        return None

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
# ==============================================================================
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    st.markdown("---")
    
    api_key_input = st.text_input("Por favor, insira sua Chave de API de Administrador:", type="password")

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

# ==============================================================================
# PAINEL PRINCIPAL
# ==============================================================================
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
        # ▼▼▼ 3. EXIBIR NOVAS COLUNAS NA TABELA DE CONTAS ▼▼▼
        # Garante que as colunas apareçam mesmo se não existirem em todos os registros
        df_accounts = pd.DataFrame(accounts)
        cols_to_show = ['name', 'cod_tri7', 'cidade', 'uf', 'id', 'created_at']
        df_accounts_display = df_accounts.reindex(columns=cols_to_show)
        st.dataframe(df_accounts_display, hide_index=True, use_container_width=True)
        
        # ▼▼▼ 4. ATUALIZAR FORMULÁRIO DE CRIAÇÃO DE CONTA ▼▼▼
        with st.expander("Criar Nova Conta de Cartório"):
            with st.form("new_account_form", clear_on_submit=True):
                new_account_name = st.text_input("Nome do Novo Cartório")
                st.markdown("###### Informações de Localização (Opcional)")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    cod_tri7 = st.number_input("Código TRI7", step=1, value=None, placeholder="Apenas números")
                with col2:
                    cidade = st.text_input("Cidade")
                with col3:
                    uf = st.text_input("UF", max_chars=2)

                if st.button("Criar Conta"):
                    if new_account_name:
                        if create_new_account(
                            new_account_name, headers,
                            cod_tri7=cod_tri7, cidade=cidade, uf=uf.upper() if uf else None
                        ):
                            st.success(f"Conta '{new_account_name}' criada!"); st.rerun()
                    else:
                        st.warning("O nome da conta não pode ser vazio.")
        
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
            
            # ▼▼▼ 5. LIMPAR FORMULÁRIO DE CRIAÇÃO DE USUÁRIO ▼▼▼
            with st.expander(f"Criar Novo Usuário para '{selected_account_name}'"):
                with st.form("new_user_form", clear_on_submit=True):
                    full_name = st.text_input("Nome Completo do Usuário")
                    email = st.text_input("Email")
                    password = st.text_input("Senha", type="password")
                    
                    if st.button("Criar Usuário"):
                        if all([full_name, email, password]):
                            if create_new_user(
                                full_name, email, password, selected_account_id, headers
                            ): 
                                st.success(f"Usuário '{full_name}' criado!")
                                st.rerun()
                        else: 
                            st.warning("Preencha os campos de Nome, Email e Senha.")
                            
# (As outras páginas permanecem sem alterações)
elif page == "Gerenciar Prompts":
    # ... (código existente) ...
    st.header("Gerenciar Catálogo de Prompts")
    prompts = get_all_prompts(headers)
    if prompts is not None:
        if prompts:
            df = pd.DataFrame(prompts)
            df_display = df[['id', 'name']].sort_values(by="id")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            prompt_options = {f"ID {p['id']} - {p['name']}": p['id'] for p in prompts}
            selected_option = st.selectbox("Selecione um prompt para editar/deletar:", options=prompt_options.keys())
            selected_id = prompt_options[selected_option]
            
            selected_prompt = next((p for p in prompts if p['id'] == selected_id), None)
            
            with st.expander(f"Editar Prompt Selecionado (ID: {selected_id})", expanded=True):
                if selected_prompt:
                    edit_name = st.text_input("Nome do Prompt", value=selected_prompt['name'], key=f"edit_name_{selected_id}")
                    edit_text = st.text_area("Texto do Prompt", value=selected_prompt['prompt_text'], height=200, key=f"edit_text_{selected_id}")
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button("Salvar Alterações", use_container_width=True, key=f"save_{selected_id}"):
                            if update_prompt(selected_id, edit_name, edit_text, headers): st.success("Prompt atualizado!"); st.rerun()
                    with col2:
                        if st.button("Deletar Prompt", type="primary", use_container_width=True, key=f"delete_{selected_id}"):
                            if delete_prompt(selected_id, headers): st.success("Prompt deletado!"); st.rerun()
        else: st.info("Nenhum prompt encontrado.")

    with st.expander("Criar Novo Prompt"):
        new_name = st.text_input("Nome do Novo Prompt", key="new_name")
        new_text = st.text_area("Texto do Novo Prompt", height=200, key="new_text")
        if st.button("Criar Prompt"):
            if new_name and new_text:
                if create_new_prompt(new_name, new_text, headers): st.success(f"Prompt '{new_name}' criado!"); st.rerun()
            else: st.warning("Preencha todos os campos.")

elif page == "Gerenciar Permissões":
    # ... (código existente) ...
    st.header("Gerenciar Permissões por Cartório")
    accounts = get_all_accounts(headers)
    prompts = get_all_prompts(headers)
    if accounts is not None and prompts is not None:
        account_names = {acc['name']: acc['id'] for acc in accounts}
        selected_name = st.selectbox("Selecione um Cartório:", options=sorted(account_names.keys()))
        selected_account_id = account_names[selected_name]
        
        st.subheader(f"Editando permissões para: {selected_name}")
        current_permissions = get_account_permissions(selected_account_id, headers)
        
        prompt_options = sorted(prompts, key=lambda p: p['id'])
        selections = [False] * len(prompt_options)

        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]

        for i, prompt in enumerate(prompt_options):
            with columns[i % 3]:
                is_checked = prompt['id'] in current_permissions
                key = f"perm_{selected_account_id}_{prompt['id']}"
                selections[i] = st.checkbox(f"ID {prompt['id']} - {prompt['name']}", value=is_checked, key=key)

        if st.button("Salvar Permissões"):
            selected_ids = [prompt_options[i]['id'] for i, selected in enumerate(selections) if selected]
            if sync_account_permissions(selected_account_id, selected_ids, headers):
                st.success("Permissões salvas com sucesso!")
                st.rerun()

elif page == "Dashboard de Faturamento":
    # ... (código existente) ...
    st.header("Dashboard de Faturamento")
    accounts = get_all_accounts(headers)
    if accounts:
        account_options = {acc['name']: acc['id'] for acc in accounts}
        selected_account_name = st.selectbox("Selecione a Conta:", options=sorted(account_options.keys()))
        selected_account_id = account_options[selected_account_name]

        today = date.today()
        default_start = today - timedelta(days=30)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data de Início", value=default_start)
        with col2:
            end_date = st.date_input("Data de Fim", value=today)

        if st.button("Gerar Relatório"):
            if start_date and end_date and selected_account_id:
                report = get_billing_report(selected_account_id, str(start_date), str(end_date), headers)
                if report:
                    st.subheader("Relatório Resumido de Consumo")
                    st.json(report)

                detailed_report = get_detailed_billing_report(selected_account_id, str(start_date), str(end_date), headers)
                if detailed_report:
                    st.subheader("Relatório Detalhado por Job")
                    st.dataframe(pd.DataFrame(detailed_report), hide_index=True)
