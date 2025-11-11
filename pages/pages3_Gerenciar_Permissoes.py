# pages/3_Gerenciar_Permissoes.py

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from admin_panel_main import headers, get_all_accounts, get_all_prompts
from admin_panel_main import get_account_permissions, sync_account_permissions

if not st.session_state.get('is_authenticated'):
    st.stop()

st.header("Gerenciar Permissões por Conta")
st.info("O bug de unificação de checkboxes foi corrigido. O sistema agora usa uma chave única para cada permissão (Conta + Prompt ID).")

accounts = get_all_accounts(headers)
prompts = get_all_prompts(headers)

if accounts and prompts:
    account_options = {acc['id']: acc['name'] for acc in accounts}
    
    # 1. Seleção de Conta
    selected_account_id_perm = st.selectbox("Selecione a conta para gerenciar:", 
                                            options=sorted(account_options.keys(), key=lambda x: account_options[x]), 
                                            format_func=lambda x: account_options[x], 
                                            key="perm_account_select")
    
    # 2. Lógica para forçar a limpeza do cache de permissões ao mudar a conta (Bugfix)
    if selected_account_id_perm != st.session_state.get('last_perm_account_id'):
        get_account_permissions.clear()
        st.session_state.last_perm_account_id = selected_account_id_perm
    
    if selected_account_id_perm:
        st.subheader(f"Configurando Prompts para: {account_options[selected_account_id_perm]}")
        current_permissions = get_account_permissions(selected_account_id_perm, headers)
        
        # 3. Layout de Checkboxes em Colunas (Melhor UX)
        num_columns = 4
        cols = st.columns(num_columns)
        all_prompt_ids = sorted(prompts, key=lambda p: p['id']) # Ordena por ID
        
        new_permissions = []
        
        st.write("Marque os prompts que a conta deve ter acesso:")
        with st.form("perm_form"):
            for i, prompt in enumerate(all_prompt_ids):
                # CHAVE ÚNICA E SÓLIDA: key=f"perm_{account_id}_{prompt_id}"
                is_checked = cols[i % num_columns].checkbox(f"{prompt['name']} (ID: {prompt['id']})", 
                                                            value=(prompt['id'] in current_permissions), 
                                                            key=f"perm_{selected_account_id_perm}_{prompt['id']}")
                if is_checked: new_permissions.append(prompt['id'])
            
            st.markdown("---")
            if st.form_submit_button("Salvar Permissões", use_container_width=True):
                if sync_account_permissions(selected_account_id_perm, new_permissions, headers):
                    st.success("Permissões atualizadas com sucesso!"); st.rerun()