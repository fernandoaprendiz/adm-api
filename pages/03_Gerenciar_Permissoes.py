# pages/3_Gerenciar_Permissoes.py (VERSÃO FINAL COM FILTRO DE CONTAS ATIVAS)

import streamlit as st
import pandas as pd
from shared_funcs import get_all_accounts, get_all_prompts
from shared_funcs import get_account_permissions, sync_account_permissions

if not st.session_state.get('is_authenticated'):
    st.stop()

API_KEY = st.session_state.api_key

st.header("Gerenciar Permissões por Conta")
st.info("O bug de unificação de checkboxes foi corrigido. O sistema agora usa uma chave única para cada permissão (Conta + Prompt ID).")

accounts = get_all_accounts(API_KEY)
prompts = get_all_prompts(API_KEY)

if accounts and prompts:
    # --- FILTRO ADICIONADO AQUI ---
    # 1. Filtra a lista para incluir apenas as contas ativas
    active_accounts = [acc for acc in accounts if acc.get('is_active', True)]
    
    # 2. Cria as opções do selectbox usando APENAS a lista de contas ativas
    account_options = {acc['id']: acc['name'] for acc in active_accounts}
    # --- FIM DO FILTRO ---
    
    if not account_options:
        st.info("Não há contas ativas para gerenciar permissões.")
        st.stop()
        
    # 3. O selectbox agora é populado apenas com contas ativas
    selected_account_id_perm = st.selectbox("Selecione a conta para gerenciar:", 
                                            options=sorted(account_options.keys(), key=lambda x: account_options[x]), 
                                            format_func=lambda x: account_options[x], 
                                            key="perm_account_select")
    
    # O restante do código permanece exatamente o mesmo, pois ele já está correto.
    
    # Lógica para forçar a limpeza do cache de permissões ao mudar a conta (Bugfix)
    if selected_account_id_perm != st.session_state.get('last_perm_account_id'):
        get_account_permissions.clear()
        st.session_state.last_perm_account_id = selected_account_id_perm
    
    if selected_account_id_perm:
        st.subheader(f"Configurando Prompts para: {account_options[selected_account_id_perm]}")
        current_permissions = get_account_permissions(selected_account_id_perm, API_KEY)
        
        # Layout de Checkboxes em Colunas (Melhor UX)
        num_columns = 4
        cols = st.columns(num_columns)
        all_prompt_ids = sorted(prompts, key=lambda p: p['id']) # Ordena por ID
        
        new_permissions = []
        
        st.write("Marque os prompts que a conta deve ter acesso:")
        with st.form("perm_form"):
            for i, prompt in enumerate(all_prompt_ids):
                # CHAVE ÚNICA E SÓLIDA
                is_checked = cols[i % num_columns].checkbox(f"{prompt['name']} (ID: {prompt['id']})", 
                                                            value=(prompt['id'] in current_permissions), 
                                                            key=f"perm_{selected_account_id_perm}_{prompt['id']}")
                if is_checked: new_permissions.append(prompt['id'])
            
            st.markdown("---")
            if st.form_submit_button("Salvar Permissões", use_container_width=True):
                if sync_account_permissions(selected_account_id_perm, new_permissions, API_KEY):
                    st.success("Permissões atualizadas com sucesso!"); st.rerun()
