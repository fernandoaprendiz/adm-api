# admin_panel_login.py (VERSÃO FINAL, COM CORREÇÃO NA EXIBIÇÃO DA API KEY)

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

# --- FUNÇÃO DE AJUDA PARA TRATAR ERROS DE API ---
def handle_api_error(error: requests.exceptions.RequestException, context: str):
    try:
        detail = error.response.json().get("detail", "Erro desconhecido.")
    except (json.JSONDecodeError, AttributeError):
        detail = error.response.text
    st.error(f"Erro ao {context}: {detail}")

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
                with st.form("new_user_form", clear_on_submit=True):
                    full_name = st.text_input("Nome Completo do Usuário")
                    email = st.text_input("Email")
                    password = st.text_input("Senha", type="password")
                    
                    # ▼▼▼ CORREÇÃO APLICADA AQUI ▼▼▼
                    if st.form_submit_button("Criar Usuário"):
                        if all([full_name, email, password]):
                            with st.spinner("Criando usuário..."):
                                # 1. Salvar a resposta da API
                                response = create_new_user(full_name, email, password, selected_account_id, headers)
                                # 2. Verificar se a resposta é válida e exibir a chave
                                if response:
                                    st.success(f"Usuário '{response['full_name']}' criado com sucesso!")
                                    st.info("API Key gerada (copie e envie ao usuário, ela não será exibida novamente):")
                                    st.code(response['api_key'])
                                    # 3. Remover o st.rerun() para permitir a exibição
                        else: 
                            st.warning("Preencha os campos de Nome, Email e Senha.")
                            
elif page == "Gerenciar Prompts":
    st.header("Gerenciar Catálogo de Prompts")
    with st.expander("Criar Novo Prompt"):
        with st.form("new_prompt_form", clear_on_submit=True):
            new_name = st.text_input("Nome do Novo Prompt")
            new_text = st.text_area("Texto do Novo Prompt", height=200)
            if st.form_submit_button("Criar Prompt"):
                if new_name and new_text:
                    if create_new_prompt(new_name, new_text, headers): st.success(f"Prompt '{new_name}' criado!"); st.rerun()
                else: st.warning("Preencha todos os campos.")
    
    st.markdown("---")
    st.subheader("Prompts Existentes")
    prompts = get_all_prompts(headers)
    if prompts:
        for prompt in prompts:
            with st.expander(f"ID {prompt['id']} - {prompt['name']}"):
                with st.form(f"form_edit_prompt_{prompt['id']}"):
                    edited_name = st.text_input("Nome", value=prompt['name'], key=f"name_{prompt['id']}")
                    edited_text = st.text_area("Texto", value=prompt['prompt_text'], height=200, key=f"text_{prompt['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Salvar Alterações", use_container_width=True):
                            if update_prompt(prompt['id'], edited_name, edited_text, headers): st.success("Prompt atualizado!"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Deletar", use_container_width=True):
                            if delete_prompt(prompt['id'], headers): st.success("Prompt deletado!"); st.rerun()
    else: st.info("Nenhum prompt encontrado.")

elif page == "Gerenciar Permissões":
    st.header("Gerenciar Permissões por Cartório")
    accounts = get_all_accounts(headers)
    prompts = get_all_prompts(headers)
    if accounts and prompts:
        account_names = {acc['name']: acc['id'] for acc in accounts}
        selected_name = st.selectbox("Selecione um Cartório:", options=sorted(account_names.keys()))
        selected_account_id = account_names[selected_name]
        
        st.subheader(f"Editando permissões para: {selected_name}")
        with st.form("permissions_form"):
            current_permissions = get_account_permissions(selected_account_id, headers)
            new_permission_ids = []
            cols = st.columns(3)
            for i, prompt in enumerate(prompts):
                with cols[i % 3]:
                    is_checked = prompt['id'] in current_permissions
                    key = f"perm_{selected_account_id}_{prompt['id']}"
                    if st.checkbox(f"ID {prompt['id']} - {prompt['name']}", value=is_checked, key=key):
                        new_permission_ids.append(prompt['id'])
            if st.form_submit_button("Salvar Permissões"):
                if sync_account_permissions(selected_account_id, new_permission_ids, headers):
                    st.success("Permissões salvas com sucesso!"); st.rerun()
    else: st.info("Crie contas e prompts antes de gerenciar permissões.")

elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    accounts = get_all_accounts(headers)
    if accounts:
        with st.form("billing_form"):
            account_options = {"Todos os Cartórios": None}
            account_options.update({acc['name']: acc['id'] for acc in accounts})
            selected_account_name = st.selectbox("Selecione a Conta:", options=account_options.keys())
            
            today = date.today()
            default_start = today - timedelta(days=30)
            col1, col2 = st.columns(2)
            with col1: start_date = st.date_input("Data de Início", value=default_start)
            with col2: end_date = st.date_input("Data de Fim", value=today)
            
            submitted = st.form_submit_button("Gerar Relatório", use_container_width=True)
        
        if submitted:
            selected_account_id = account_options[selected_account_name]
            if start_date and end_date:
                with st.spinner("Gerando relatório... Por favor, aguarde."):
                    report_data = get_master_billing_report(str(start_date), str(end_date), selected_account_id, headers)
                
                if report_data and report_data.get('breakdown'):
                    st.session_state['detailed_report_data'] = report_data['breakdown']
                    st.subheader("Resumo do Período"); total_jobs = len(report_data['breakdown']); total_cost = sum(Decimal(item['cost_brl']) for item in report_data['breakdown'])
                    col_resumo1, col_resumo2 = st.columns(2)
                    col_resumo1.metric(label="Total de Jobs Processados", value=total_jobs)
                    col_resumo2.metric(label="Custo Total (R$)", value=f"{total_cost:.2f}")
                else:
                    st.info("Nenhum dado de faturamento encontrado para o período e conta selecionados.")
                    if 'detailed_report_data' in st.session_state: del st.session_state['detailed_report_data']

        if 'detailed_report_data' in st.session_state and st.session_state['detailed_report_data']:
            st.markdown("---"); st.subheader("Exportar Relatório Detalhado")
            df = pd.DataFrame(st.session_state['detailed_report_data'])
            df_export = df.rename(columns={
                'job_id': 'ID do Job', 
                'created_at': 'Data', 
                'account_name': 'Cartório', 
                'user_name': 'Usuário', 
                'prompt_name': 'Prompt', 
                'display_name': 'Modelo', 
                'cost_brl': 'Custo (R$)'
            })
            
            final_columns = ['Data', 'Cartório', 'Usuário', 'ID do Job', 'Prompt', 'Modelo', 'Custo (R$)']
            df_export = df_export[final_columns]
            df_export['Data'] = pd.to_datetime(df_export['Data']).dt.strftime('%d/%m/%Y %H:%M:%S')
            df_export['Custo (R$)'] = df_export['Custo (R$)'].astype(float)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='RelatorioFaturamento')
                worksheet = writer.sheets['RelatorioFaturamento']
                for i, col in enumerate(df_export.columns):
                    column_len = df_export[col].astype(str).str.len().max()
                    column_len = max(column_len, len(col)) + 2
                    worksheet.set_column(i, i, column_len)

            st.download_button(label="Baixar Relatório Detalhado (.xlsx)", data=output.getvalue(), file_name=f"relatorio_{start_date}_a_{end_date}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
