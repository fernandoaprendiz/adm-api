# admin_panel.py (VERSÃO FINAL, COMPLETA E CORRIGIDA)

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
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None

def create_new_account(name: str, cod_tri7: Optional[int], cidade: Optional[str], uf: Optional[str], headers: Dict):
    payload = {"name": name}
    if cod_tri7: payload["cod_tri7"] = cod_tri7
    if cidade: payload["cidade"] = cidade
    if uf: payload["uf"] = uf
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=headers, json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar conta"); return None

@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, headers: Dict) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None

def create_new_user(full_name: str, email: str, password: str, account_id: int, headers: Dict):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=headers, json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar usuário"); return None

def set_account_status(account_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=headers); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, f"mudar status da conta"); return False

def set_user_status(user_id: int, is_active: bool, headers: Dict) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/users/{user_id}/status?active_status={is_active}", headers=headers); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, f"mudar status do usuário"); return False

def regenerate_api_key(user_id: int, headers: Dict) -> Optional[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/admin/users/{user_id}/regenerate-api-key", headers=headers); response.raise_for_status()
        return response.json().get("api_key")
    except requests.exceptions.RequestException as e: handle_api_error(e, "regenerar chave de API"); return None

# Funções de Prompts e Permissões (CORRIGIDAS)
@st.cache_data(ttl=60)
def get_all_prompts(headers: Dict):
    try: response = requests.get(f"{API_BASE_URL}/admin/prompts/", headers=headers); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar prompts"); return None

def create_new_prompt(name: str, text: str, headers: Dict):
    try: response = requests.post(f"{API_BASE_URL}/admin/prompts/", headers=headers, json={"name": name, "prompt_text": text}); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar prompt"); return None

def update_prompt_details(prompt_id: int, name: str, text: str, headers: Dict):
    try: response = requests.put(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=headers, json={"name": name, "prompt_text": text}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "atualizar prompt"); return False

def delete_prompt(prompt_id: int, headers: Dict):
    try: response = requests.delete(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=headers); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "deletar prompt"); return False

@st.cache_data(ttl=60)
def get_account_permissions(account_id: int, headers: Dict):
    try: 
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers); response.raise_for_status()
        return response.json().get("prompt_ids", [])
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar permissões"); return []

def sync_account_permissions(account_id: int, prompt_ids: List[int], headers: Dict):
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=headers, json={"prompt_ids": prompt_ids})
        response.raise_for_status()
        get_account_permissions.clear() # Limpa o cache após salvar para forçar a próxima leitura
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "salvar permissões"); return False

# Função de Faturamento
def get_master_billing_report(start_date: str, end_date: str, account_id: Optional[int], headers: Dict):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id is not None: params["account_id"] = account_id
    try:
        response = requests.get(f"{API_BASE_URL}/billing/report/", headers=headers, params=params); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório"); return None

# --- INICIALIZAÇÃO DA SESSÃO ---
st.session_state.setdefault('is_authenticated', False)
st.session_state.setdefault('api_key', "")
st.session_state.setdefault('new_api_key_info', None)
st.session_state.setdefault('confirm_action', None)
st.session_state.setdefault('last_perm_account_id', None)

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
                        st.session_state.is_authenticated = True; st.session_state.api_key = api_key_input; st.rerun()
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

# --- Gerenciar Contas e Usuários ---
if page == "Gerenciar Contas e Usuários":
    # Exibe a nova chave de API no contexto da página
    if st.session_state.new_api_key_info:
        user_name, new_key = st.session_state.new_api_key_info
        st.success(f"Nova API Key gerada para '{user_name}'! Copie e envie ao usuário.")
        st.code(new_key)
        st.session_state.new_api_key_info = None

    accounts = get_all_accounts(headers)
    if accounts:
        st.header("Visão Geral das Contas"); st.dataframe(pd.DataFrame(accounts)[['name', 'is_active', 'id', 'created_at']], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.header("Gerenciamento Detalhado")
        account_options = {acc['id']: acc['name'] for acc in accounts}
        selected_account_id = st.selectbox("Selecione uma conta para gerenciar:", options=sorted(account_options.keys(), key=lambda x: account_options[x]), format_func=lambda x: f"{account_options[x]} (ID: {x})")
        
        selected_account = next((acc for acc in accounts if acc['id'] == selected_account_id), None)
        if selected_account:
            st.subheader(f"Ações para a Conta: '{selected_account['name']}'")
            is_active = selected_account.get('is_active', True)
            action_label = "🔴 Desativar" if is_active else "🟢 Reativar"
            
            if st.button(f"{action_label} Conta '{selected_account['name']}'"):
                st.session_state.confirm_action = ("account_status", selected_account_id, not is_active, selected_account['name'])
            
            # Lógica de confirmação para status da conta
            if st.session_state.confirm_action and st.session_state.confirm_action[0:2] == ("account_status", selected_account_id):
                _, acc_id, new_status, name = st.session_state.confirm_action
                action_word = "DESATIVAR" if new_status is False else "REATIVAR"
                st.warning(f"**Atenção:** Você tem certeza que deseja {action_word} a conta '{name}'?")
                if st.button("Sim, confirmar", key="confirm_acc_status"):
                    if set_account_status(acc_id, new_status, headers):
                        st.success("Status da conta atualizado."); st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                    else: st.session_state.confirm_action = None
                if st.button("Cancelar", key="cancel_acc_status"): st.session_state.confirm_action = None; st.rerun()

            st.markdown("---")
            st.subheader(f"Usuários da Conta: '{selected_account['name']}'")
            users = get_users_for_account(selected_account_id, headers)
            if users:
                st.dataframe(pd.DataFrame(users)[['full_name', 'email', 'is_active', 'id']], use_container_width=True, hide_index=True)
                user_options = {user['id']: user['full_name'] for user in users}
                selected_user_id = st.selectbox("Selecione um usuário:", options=sorted(user_options.keys(), key=lambda x: user_options[x]), format_func=lambda x: f"{user_options[x]} (ID: {x})")
                
                selected_user = next((user for user in users if user['id'] == selected_user_id), None)
                if selected_user:
                    is_user_active = selected_user.get('is_active', True)
                    user_action_label = "Desativar" if is_user_active else "Reativar"
                    
                    col1, col2 = st.columns(2)
                    if col1.button(f"{user_action_label} Usuário"): st.session_state.confirm_action = ("user_status", selected_user_id, not is_user_active, selected_user['full_name'])
                    if col2.button("🔑 Regenerar Chave"): st.session_state.confirm_action = ("regen_key", selected_user_id, selected_user['full_name'])

                    # Lógica de confirmação para ações do usuário
                    if st.session_state.confirm_action and st.session_state.confirm_action[1] == selected_user_id:
                        action_type, user_id, name = st.session_state.confirm_action[0], st.session_state.confirm_action[1], st.session_state.confirm_action[-1]
                        
                        if action_type == "user_status":
                            new_status = st.session_state.confirm_action[2]
                            action_word = "DESATIVAR" if not new_status else "REATIVAR"
                            st.warning(f"Tem certeza que deseja {action_word} o usuário '{name}'?")
                            if st.button("Sim, confirmar", key="confirm_user_status"):
                                if set_user_status(user_id, new_status, headers):
                                    st.success("Status do usuário atualizado."); st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                                else: st.session_state.confirm_action = None
                            if st.button("Cancelar", key="cancel_user_status"): st.session_state.confirm_action = None; st.rerun()
                        
                        elif action_type == "regen_key":
                            st.warning(f"Isso invalidará a chave antiga do usuário '{name}'. Continuar?")
                            if st.button("Sim, regenerar", key="confirm_regen"):
                                new_key = regenerate_api_key(user_id, headers)
                                if new_key:
                                    st.session_state.new_api_key_info = (name, new_key)
                                    st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                                else: st.session_state.confirm_action = None
                            if st.button("Cancelar", key="cancel_regen"): st.session_state.confirm_action = None; st.rerun()

            with st.expander(f"➕ Criar Novo Usuário para '{selected_account['name']}'"):
                with st.form("new_user_form", clear_on_submit=True):
                    full_name, email, password = st.text_input("Nome Completo"), st.text_input("Email"), st.text_input("Senha", type="password")
                    if st.form_submit_button("Criar Usuário"):
                        if all([full_name, email, password]):
                            response = create_new_user(full_name, email, password, selected_account_id, headers)
                            if response: st.session_state.new_api_key_info = (response['full_name'], response.get('api_key')); st.cache_data.clear(); st.rerun()
                        else: st.warning("Preencha todos os campos.")

    with st.expander("➕ Criar Nova Conta"):
        with st.form("new_account_form", clear_on_submit=True):
            new_account_name = st.text_input("Nome do Novo Cartório")
            
            st.markdown("###### Informações de Localização (Opcional)")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1: cod_tri7 = st.number_input("Código TRI7", step=1, value=None, placeholder="Apenas números")
            with col2: cidade = st.text_input("Município")
            with col3: uf = st.text_input("UF", max_chars=2)

            if st.form_submit_button("Criar Conta"):
                if new_account_name:
                    # Limpa campos opcionais se estiverem vazios
                    cidade_clean = cidade if cidade else None
                    uf_clean = uf.upper() if uf else None
                    if create_new_account(new_account_name, cod_tri7, cidade_clean, uf_clean, headers): 
                        st.success(f"Conta '{new_account_name}' criada!"); st.cache_data.clear(); st.rerun()
                else: st.warning("O nome da conta não pode ser vazio.")

# --- Gerenciar Prompts ---
elif page == "Gerenciar Prompts":
    st.header("Gerenciar Prompts")
    prompts = get_all_prompts(headers)
    if prompts:
        st.dataframe(pd.DataFrame(prompts)[['id', 'name']], use_container_width=True, hide_index=True)
        
        prompt_options = {p['id']: p['name'] for p in prompts}
        selected_prompt_id = st.selectbox("Selecione um prompt para editar ou deletar:", options=sorted(prompt_options.keys(), key=lambda x: prompt_options[x]), format_func=lambda x: f"{prompt_options[x]} (ID: {x})")
        
        selected_prompt = next((p for p in prompts if p['id'] == selected_prompt_id), None)
        
        if selected_prompt:
            st.markdown("---")
            st.subheader(f"Editar Prompt: {selected_prompt['name']}")
            with st.form("edit_prompt_form"):
                edited_name = st.text_input("Nome do Prompt", value=selected_prompt['name'])
                edited_text = st.text_area("Texto do Prompt", value=selected_prompt['prompt_text'], height=300)
                
                col1, col2 = st.columns(2)
                if col1.form_submit_button("Salvar Alterações", use_container_width=True):
                    if update_prompt_details(selected_prompt_id, edited_name, edited_text, headers):
                        st.success("Prompt atualizado!"); st.cache_data.clear(); st.rerun()
                if col2.form_submit_button("Deletar Prompt", use_container_width=True):
                    st.session_state.confirm_action = ("delete_prompt", selected_prompt_id, selected_prompt['name'])
            
            # Lógica de confirmação para deletar prompt
            if st.session_state.confirm_action and st.session_state.confirm_action[0:2] == ("delete_prompt", selected_prompt_id):
                _, prompt_id, name = st.session_state.confirm_action
                st.warning(f"**Atenção:** Você tem certeza que deseja DELETAR o prompt '{name}'? Esta ação não pode ser desfeita.")
                if st.button("Sim, DELETAR", key="confirm_delete"):
                    if delete_prompt(prompt_id, headers): st.success("Prompt deletado."); st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                if st.button("Cancelar", key="cancel_delete"): st.session_state.confirm_action = None; st.rerun()

    with st.expander("➕ Criar Novo Prompt"):
        with st.form("new_prompt_form", clear_on_submit=True):
            new_prompt_name = st.text_input("Nome do Novo Prompt")
            new_prompt_text = st.text_area("Texto do Novo Prompt", height=200)
            if st.form_submit_button("Criar Prompt"):
                if new_prompt_name and new_prompt_text:
                    if create_new_prompt(new_prompt_name, new_prompt_text, headers): st.success("Novo prompt criado!"); st.cache_data.clear(); st.rerun()
                else: st.warning("Preencha o nome e o texto do prompt.")

# --- Gerenciar Permissões ---
elif page == "Gerenciar Permissões":
    st.header("Gerenciar Permissões por Conta")
    
    accounts = get_all_accounts(headers)
    prompts = get_all_prompts(headers)
    
    if accounts and prompts:
        account_options = {acc['id']: acc['name'] for acc in accounts}
        
        # Lógica para forçar a limpeza do cache de permissões ao mudar a conta
        selected_account_id_perm = st.selectbox("Selecione a conta para gerenciar:", options=sorted(account_options.keys(), key=lambda x: account_options[x]), format_func=lambda x: account_options[x], key="perm_account_select")
        
        if selected_account_id_perm != st.session_state.last_perm_account_id:
            get_account_permissions.clear()
            st.session_state.last_perm_account_id = selected_account_id_perm
        
        if selected_account_id_perm:
            st.subheader(f"Configurando Prompts para: {account_options[selected_account_id_perm]}")
            current_permissions = get_account_permissions(selected_account_id_perm, headers)
            
            num_columns = 4
            cols = st.columns(num_columns)
            all_prompt_ids = sorted(prompts, key=lambda p: p['name'])
            
            new_permissions = []
            
            st.write("Marque os prompts que a conta deve ter acesso:")
            for i, prompt in enumerate(all_prompt_ids):
                # O uso de key=f"perm_{selected_account_id_perm}_{prompt['id']}" garante que a chave é única por CONTA+PROMPT.
                is_checked = cols[i % num_columns].checkbox(f"{prompt['name']} (ID: {prompt['id']})", value=(prompt['id'] in current_permissions), key=f"perm_{selected_account_id_perm}_{prompt['id']}")
                if is_checked: new_permissions.append(prompt['id'])
            
            st.markdown("---")
            if st.button("Salvar Permissões", use_container_width=True):
                if sync_account_permissions(selected_account_id_perm, new_permissions, headers):
                    st.success("Permissões atualizadas com sucesso!"); st.rerun()

# --- Dashboard de Faturamento ---
elif page == "Dashboard de Faturamento":
    st.header("Dashboard de Faturamento")
    accounts = get_all_accounts(headers)
    if accounts:
        with st.form("billing_form"):
            account_options_billing = {"Todas as Contas (Resumo)": None}
            account_options_billing.update({acc['name']: acc['id'] for acc in accounts})
            selected_account_name = st.selectbox("Selecione a Conta:", options=account_options_billing.keys())
            
            today = date.today()
            default_start = today - timedelta(days=30)
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Data de Início", value=default_start)
            end_date = col2.date_input("Data de Fim", value=today)
            
            submitted = st.form_submit_button("Gerar Relatório", use_container_width=True)
        
        if submitted:
            selected_account_id_billing = account_options_billing[selected_account_name]
            report_id = selected_account_id_billing 
            
            if start_date and end_date:
                with st.spinner("Gerando relatório..."):
                    report_data = get_master_billing_report(str(start_date), str(end_date), report_id, headers)
                
                if report_data and report_data.get('by_model'):
                    st.session_state['detailed_report_data'] = report_data
                    
                    st.subheader(f"Resumo do Período para: {selected_account_name}")
                    summary = report_data.get('summary', {})
                    by_model = report_data.get('by_model', [])

                    col_resumo1, col_resumo2 = st.columns(2)
                    col_resumo1.metric(label="Total de Jobs Processados", value=f"{summary.get('total_jobs', 0):,}")
                    col_resumo2.metric(label="Total de Tokens Consumidos", value=f"{summary.get('total_tokens', 0):,}")

                    st.subheader("Consumo Detalhado por Modelo")
                    df_report = pd.DataFrame(by_model)
                    st.dataframe(df_report, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum dado de faturamento encontrado para o período e conta selecionados.")
                    if 'detailed_report_data' in st.session_state: del st.session_state['detailed_report_data']

        # Lógica de Exportação do Relatório (Com correção para o formato desejado)
        if 'detailed_report_data' in st.session_state:
            st.markdown("---")
            st.subheader("Exportar Relatório")
            
            # --- CORREÇÃO DA EXPORTAÇÃO: Simulando os campos detalhados que a API deve fornecer ---
            # Como a API que você forneceu só dá o resumo, esta parte é um placeholder com lógica
            # para o formato que você pediu.

            # Gerando um DataFrame simulado com base no RESUMO para a exportação
            df_resumo = pd.DataFrame(st.session_state['detailed_report_data']['by_model'])
            
            # Simulação de dados detalhados (Isto precisa de um endpoint de API, mas vamos preparar o formato)
            # Para manter a função de download operacional e com o formato que você pediu:
            
            # ATENÇÃO: Se o seu endpoint /billing/report/ retornar uma lista de JOBS (Detalhe), use-o aqui.
            # Como ele retorna um resumo (by_model), vamos simular o formato de exportação ideal para você.
            
            # Como não temos os dados detalhados, faremos uma exportação do RESUMO formatado.
            df_export = df_resumo.rename(columns={
                'model': 'Modelo',
                'tokens': 'Tokens Consumidos',
                'jobs': 'Jobs Processados'
            })
            
            # Se você tiver um endpoint de API para dados detalhados (jobs linha a linha), você deve chamá-lo aqui.
            # Ex: detailed_jobs = get_detailed_billing_jobs(...)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='ResumoFaturamento')
                worksheet = writer.sheets['ResumoFaturamento']
                for i, col in enumerate(df_export.columns):
                    column_len = max(df_export[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
            
            period_str = st.session_state['detailed_report_data']['period']
            file_name_str = f"relatorio_resumo_completo_{period_str['start']}_a_{period_str['end']}.xlsx"

            st.download_button(label="📥 Baixar Relatório Resumido (.xlsx)", data=output.getvalue(), file_name=file_name_str, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
