# admin_panel_login.py (VERSÃO FINAL COM NOVO DASHBOARD DE FATURAMENTO)

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

# --- FUNÇÃO DE AJUDA PARA TRATAR ERROS DE API ---
def handle_api_error(error: requests.exceptions.RequestException, context: str):
    try:
        detail = error.response.json().get("detail", "Erro desconhecido.")
    except (json.JSONDecodeError, AttributeError):
        detail = error.response.text
    st.error(f"Erro ao {context}: {detail}")

# --- FUNÇÕES DE API ---
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
def create_new_account(name: str, headers: Dict, cod_tri7: Optional[int], cidade: Optional[str], uf: Optional[str]):
    payload = {"name": name, "cod_tri7": cod_tri7, "cidade": cidade, "uf": uf}
    payload_clean = {k: v for k, v in payload.items() if v is not None and v != ""}
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json=payload_clean)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar conta"); return None
def get_users_for_account(account_id: int, headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None
def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar usuário"); return None

# ▼▼▼ NOVA FUNÇÃO PARA O RELATÓRIO MESTRE ADICIONADA AQUI ▼▼▼
def get_master_billing_report(start_date: str, end_date: str, account_id: Optional[int], headers: Dict):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id:
        params["account_id"] = account_id
    
    try:
        response = requests.get(f"{API_BASE_URL}/admin/billing/master-report", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "gerar relatório mestre")
        return None

# --- INICIALIZAÇÃO DA SESSÃO ---
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""

# --- INTERFACE ---
st.set_page_config(layout="wide", page_title="Painel de Gestão SetDoc AI")

# TELA DE LOGIN (sem alterações)
if not st.session_state.is_authenticated:
    st.title("Acesso ao Painel de Gestão - SetDoc AI")
    # ... (código de login existente)
    st.stop()

# PAINEL PRINCIPAL
st.title("Painel de Gestão - SetDoc AI")
headers = {"x-api-key": st.session_state.api_key}

st.sidebar.header("Navegação")
page = st.sidebar.radio("Escolha uma página", ["Gerenciar Contas e Usuários", "Gerenciar Prompts", "Gerenciar Permissões", "Dashboard de Faturamento"])

def logout():
    st.session_state.is_authenticated = False
    st.session_state.api_key = ""
st.sidebar.button("Sair (Logout)", on_click=logout)

if page == "Gerenciar Contas e Usuários":
    # ... (código existente, sem alterações)
    pass 
elif page == "Gerenciar Prompts":
    # ... (código existente, sem alterações)
    pass
elif page == "Gerenciar Permissões":
    # ... (código existente, sem alterações)
    pass
# ▼▼▼ PÁGINA DE FATURAMENTO COMPLETAMENTE REFEITA ▼▼▼
elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    
    accounts = get_all_accounts(headers)
    if accounts:
        # Adiciona a opção "Todos os Cartórios"
        account_options = {"Todos os Cartórios": None}
        account_options.update({acc['name']: acc['id'] for acc in accounts})
        
        selected_account_name = st.selectbox("Selecione a Conta:", options=account_options.keys())
        selected_account_id = account_options[selected_account_name]

        today = date.today()
        default_start = today - timedelta(days=30)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data de Início", value=default_start)
        with col2:
            end_date = st.date_input("Data de Fim", value=today)

        if st.button("Gerar Relatório", use_container_width=True):
            if start_date and end_date:
                with st.spinner("Gerando relatório... Por favor, aguarde."):
                    report_data = get_master_billing_report(str(start_date), str(end_date), selected_account_id, headers)
                
                if report_data and report_data.get('breakdown'):
                    # Salva os dados no estado da sessão para o botão de download usar
                    st.session_state['detailed_report_data'] = report_data['breakdown']
                    
                    # --- Exibe o Resumo ---
                    st.subheader("Resumo do Período")
                    total_jobs = len(report_data['breakdown'])
                    total_cost = sum(Decimal(item['cost_brl']) for item in report_data['breakdown'])
                    
                    col_resumo1, col_resumo2 = st.columns(2)
                    with col_resumo1:
                        st.metric(label="Total de Jobs Processados", value=total_jobs)
                    with col_resumo2:
                        st.metric(label="Custo Total (R$)", value=f"{total_cost:.2f}")

                else:
                    st.info("Nenhum dado de faturamento encontrado para o período e conta selecionados.")
                    # Limpa o estado da sessão se não houver dados
                    if 'detailed_report_data' in st.session_state:
                        del st.session_state['detailed_report_data']

    # --- Lógica do Botão de Download (fora do "if st.button") ---
    if 'detailed_report_data' in st.session_state and st.session_state['detailed_report_data']:
        st.markdown("---")
        st.subheader("Exportar Relatório Detalhado")
        
        df = pd.DataFrame(st.session_state['detailed_report_data'])
        
        # Renomear e reordenar colunas para o arquivo final
        df_export = df.rename(columns={
            'job_id': 'ID do Job',
            'created_at': 'Data de Processamento',
            'account_name': 'Cartório',
            'user_name': 'Usuário',
            'prompt_name': 'Prompt Utilizado',
            'display_name': 'Modelo Utilizado',
            'cost_brl': 'Custo (R$)'
        })
        
        # Selecionar a ordem final das colunas
        final_columns = ['Data de Processamento', 'Cartório', 'Usuário', 'ID do Job', 'Prompt Utilizado', 'Modelo Utilizado', 'Custo (R$)']
        df_export = df_export[final_columns]
        
        # Formatar a coluna de data para um formato mais legível
        df_export['Data de Processamento'] = pd.to_datetime(df_export['Data de Processamento']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Converter custo para float para garantir a formatação correta
        df_export['Custo (R$)'] = df_export['Custo (R$)'].astype(float)

        # Gerar o arquivo Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='RelatorioFaturamento')
            # Auto-ajuste da largura das colunas
            for i, col in enumerate(df_export.columns):
                writer.sheets['RelatorioFaturamento'].set_column(i, i, len(col) + 2)

        st.download_button(
            label="Clique para Baixar Relatório Detalhado (.xlsx)",
            data=output.getvalue(),
            file_name=f"relatorio_detalhado_{start_date}_a_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
