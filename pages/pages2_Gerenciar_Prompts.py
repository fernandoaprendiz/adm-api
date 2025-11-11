# pages/2_Gerenciar_Prompts.py

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from admin_panel_main import headers, get_all_prompts
# Importa as funções de CRUD de prompts que foram definidas no arquivo principal
from admin_panel_main import create_new_prompt, update_prompt_details, delete_prompt

if not st.session_state.get('is_authenticated'):
    st.stop()

st.header("Gerenciar Prompts")
prompts = get_all_prompts(headers)
if prompts:
    # Ordena por ID crescente, como solicitado
    df_prompts = pd.DataFrame(prompts).sort_values(by='id', ascending=True)
    st.dataframe(df_prompts[['id', 'name']], use_container_width=True, hide_index=True)
    
    prompt_options = {p['id']: p['name'] for p in prompts}
    # Ordena as opções do selectbox por ID, que é o campo mais estável
    selected_prompt_id = st.selectbox("Selecione um prompt para editar ou deletar:", 
                                      options=sorted(prompt_options.keys(), key=lambda x: x), 
                                      format_func=lambda x: f"{prompt_options[x]} (ID: {x})")
    
    selected_prompt = next((p for p in prompts if p['id'] == selected_prompt_id), None)
    
    if selected_prompt:
        st.markdown("---")
        st.subheader(f"Editar Prompt: {selected_prompt['name']}")
        
        # O formulário de edição só aparece após a seleção
        with st.form("edit_prompt_form"):
            edited_name = st.text_input("Nome do Prompt", value=selected_prompt['name'])
            edited_text = st.text_area("Texto do Prompt", value=selected_prompt['prompt_text'], height=300)
            
            col1, col2 = st.columns(2)
            if col1.form_submit_button("Salvar Alterações", use_container_width=True):
                if update_prompt_details(selected_prompt_id, edited_name, edited_text, headers):
                    st.success("Prompt atualizado!"); get_all_prompts.clear(); st.rerun()
            if col2.form_submit_button("Deletar Prompt", use_container_width=True):
                st.session_state.confirm_action = ("delete_prompt", selected_prompt_id, selected_prompt['name'])
        
        # Lógica de confirmação para deletar prompt
        if st.session_state.confirm_action and st.session_state.confirm_action[0:2] == ("delete_prompt", selected_prompt_id):
            _, prompt_id, name = st.session_state.confirm_action
            st.warning(f"**Atenção:** Você tem certeza que deseja DELETAR o prompt '{name}'? Esta ação não pode ser desfeita.")
            if st.button("Sim, DELETAR", key="confirm_delete"):
                if delete_prompt(prompt_id, headers): 
                    st.success("Prompt deletado."); get_all_prompts.clear(); st.session_state.confirm_action = None; st.rerun()
            if st.button("Cancelar", key="cancel_delete"): st.session_state.confirm_action = None; st.rerun()

with st.expander("➕ Criar Novo Prompt"):
    with st.form("new_prompt_form", clear_on_submit=True):
        new_prompt_name = st.text_input("Nome do Novo Prompt")
        new_prompt_text = st.text_area("Texto do Novo Prompt", height=200)
        if st.form_submit_button("Criar Prompt"):
            if new_prompt_name and new_prompt_text:
                if create_new_prompt(new_prompt_name, new_prompt_text, headers): 
                    st.success("Novo prompt criado!"); get_all_prompts.clear(); st.rerun()
            else: st.warning("Preencha o nome e o texto do prompt.")