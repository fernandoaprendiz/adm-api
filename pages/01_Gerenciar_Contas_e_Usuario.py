# pages/1_Gerenciar_Contas_e_Usuários.py (CORRIGIDO)

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

# Importa todas as funções do módulo compartilhado
from shared_funcs import (
    get_all_accounts, get_users_for_account, create_new_account, 
    set_account_status, set_user_status, regenerate_api_key, create_new_user
)

if not st.session_state.get('is_authenticated'):
    st.stop()

API_KEY = st.session_state.api_key

# Exibe a nova chave de API no contexto da página
if st.session_state.new_api_key_info:
    user_name, new_key = st.session_state.new_api_key_info
    st.success(f"Nova API Key gerada para '{user_name}'! Copie e envie ao usuário.")
    st.code(new_key)
    st.session_state.new_api_key_info = None

st.header("Gerenciar Contas (Cartórios)")
accounts = get_all_accounts(API_KEY)
if accounts:
    # FILTRO DE VISIBILIDADE: Apenas contas ativas para a tabela principal
    df_accounts = pd.DataFrame(accounts)
    df_accounts_active = df_accounts[df_accounts['is_active'] == True]
    st.subheader("Contas Ativas (Visão Geral)")
    
    display_cols = ['name', 'is_active', 'cidade', 'uf', 'id', 'created_at']
    st.dataframe(df_accounts_active[display_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.header("Gerenciamento Detalhado (Ativação/Desativação)")
    # USAMOS A LISTA COMPLETA AQUI para que o admin possa REATIVAR uma conta
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
                if set_account_status(acc_id, new_status, API_KEY):
                    st.success("Status da conta atualizado."); st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                else: st.session_state.confirm_action = None
            if st.button("Cancelar", key="cancel_acc_status"): st.session_state.confirm_action = None; st.rerun()

        st.markdown("---")
        st.subheader(f"Usuários da Conta: '{selected_account['name']}'")
        users = get_users_for_account(selected_account_id, API_KEY)
        
        # --- CORREÇÃO DO BUG: O botão de criar usuário foi movido para fora do 'if users:' ---
        
        if users:
            # FILTRO DE VISIBILIDADE: Apenas usuários ativos para a tabela
            df_users = pd.DataFrame(users)
            df_users_active = df_users[df_users['is_active'] == True]
            st.dataframe(df_users_active[['full_name', 'email', 'is_active', 'id']], use_container_width=True, hide_index=True)

            # USAMOS A LISTA COMPLETA AQUI para que o admin possa REATIVAR um usuário
            user_options_full = {user['id']: user['full_name'] for user in users}
            selected_user_id = st.selectbox("Selecione um usuário para gerenciar:", options=sorted(user_options_full.keys(), key=lambda x: user_options_full[x]), format_func=lambda x: f"{user_options_full[x]} (ID: {x})")
            
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
                            if set_user_status(user_id, new_status, API_KEY):
                                st.success("Status do usuário atualizado."); st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                            else: st.session_state.confirm_action = None
                        if st.button("Cancelar", key="cancel_user_status"): st.session_state.confirm_action = None; st.rerun()
                    
                    elif action_type == "regen_key":
                        st.warning(f"Isso invalidará a chave antiga do usuário '{name}'. Continuar?")
                        if st.button("Sim, regenerar", key="confirm_regen"):
                            new_key = regenerate_api_key(user_id, API_KEY)
                            if new_key:
                                st.session_state.new_api_key_info = (name, new_key)
                                st.cache_data.clear(); st.session_state.confirm_action = None; st.rerun()
                            else: st.session_state.confirm_action = None
                        if st.button("Cancelar", key="cancel_regen"): st.session_state.confirm_action = None; st.rerun()
        else:
            st.info("Nenhum usuário nesta conta. Crie um novo abaixo.")

        with st.expander(f"➕ Criar Novo Usuário para '{selected_account['name']}'"):
            with st.form("new_user_form", clear_on_submit=True):
                full_name, email, password = st.text_input("Nome Completo"), st.text_input("Email"), st.text_input("Senha", type="password")
                if st.form_submit_button("Criar Usuário"):
                    if all([full_name, email, password]):
                        response = create_new_user(full_name, email, password, selected_account_id, API_KEY)
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
                    cidade_clean = cidade if cidade else None
                    uf_clean = uf.upper() if uf else None
                    cod_tri7_clean = int(cod_tri7) if cod_tri7 else None
                    if create_new_account(new_account_name, cod_tri7_clean, cidade_clean, uf_clean, API_KEY): 
                        st.success(f"Conta '{new_account_name}' criada!"); st.cache_data.clear(); st.rerun()
                else: st.warning("O nome da conta não pode ser vazio.")
