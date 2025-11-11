# pages/4_Dashboard_Faturamento.py (ALTERAÇÃO MÍNIMA PARA NOMES AMIGÁVEIS)

import streamlit as st
import pandas as pd
import io
from datetime import date, timedelta
from decimal import Decimal
from shared_funcs import get_all_accounts, get_master_billing_report, get_detailed_billing_jobs

if not st.session_state.get('is_authenticated'):
    st.stop()

API_KEY = st.session_state.api_key

st.header("Dashboard de Faturamento")
accounts = get_all_accounts(API_KEY)
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
                detailed_jobs = get_detailed_billing_jobs(str(start_date), str(end_date), report_id, API_KEY)
                summary_report = get_master_billing_report(str(start_date), str(end_date), report_id, API_KEY)

            if detailed_jobs and summary_report and summary_report.get('by_model'):
                st.session_state['billing_report_data'] = {
                    'summary': summary_report,
                    'jobs_breakdown': detailed_jobs,
                    'period': summary_report.get('period', {})
                }
            else:
                st.info("Nenhum dado de faturamento encontrado para o período e conta selecionados.")
                st.session_state.billing_report_data = None

    if st.session_state.billing_report_data:
        report_data = st.session_state.billing_report_data
        summary = report_data['summary'].get('summary', {})
        by_model = report_data['summary'].get('by_model', [])
        
        st.subheader(f"Resumo do Período para: {selected_account_name}")
        col_resumo1, col_resumo2 = st.columns(2)
        col_resumo1.metric(label="Total de Jobs Processados", value=f"{summary.get('total_jobs', 0):,}")
        col_resumo2.metric(label="Total de Tokens Consumidos", value=f"{summary.get('total_tokens', 0):,}")

        if by_model:
            st.subheader("Consumo Detalhado por Modelo")
            df_report = pd.DataFrame(by_model)
            
            # --- ADICIONADO: MAPA DE TRADUÇÃO DE NOMES ---
            model_name_map = {
                "gemini-2.5-flash-lite": "Modelo Ultra",
                "gemini-2.5-flash": "Modelo Fast",
                "gemini-2.5-pro": "Modelo Pro",
            }
            # Substitui os nomes técnicos pelos amigáveis, mantendo o original se não houver mapa
            df_report['model'] = df_report['model'].map(model_name_map).fillna(df_report['model'])
            # Renomeia a coluna para uma melhor exibição
            df_report = df_report.rename(columns={'model': 'Modelo'})
            # --- FIM DA ADIÇÃO ---
            
            st.dataframe(df_report, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Exportar Relatório Detalhado")
        
        # --- LÓGICA DE EXPORTAÇÃO (sem alterações) ---
        df_jobs = pd.DataFrame(report_data['jobs_breakdown'])

        df_jobs = df_jobs.rename(columns={
            'created_at': 'Data', 
            'account_name': 'Cartório', 
            'user_name': 'Usuário', 
            'job_id': 'ID do Job', 
            'prompt_name': 'Prompt', 
            'model_display_name': 'Modelo', 
            'cost_brl': 'Custo (R$)',
            'total_tokens': 'Tokens Brutos'
        })

        df_jobs['Data'] = pd.to_datetime(df_jobs['Data']).dt.strftime('%d/%m/%Y %H:%M:%S')
        df_jobs['Custo (R$)'] = df_jobs['Custo (R$)'].astype(float).round(8)

        final_columns = ['Data', 'Cartório', 'Usuário', 'ID do Job', 'Prompt', 'Modelo', 'Custo (R$)', 'Tokens Brutos']
        df_export = df_jobs.reindex(columns=final_columns)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='RelatorioFaturamento')
            worksheet = writer.sheets['RelatorioFaturamento']
            for i, col in enumerate(df_export.columns):
                column_len = max(df_export[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)
        
        period_str = report_data['period']
        file_name_str = f"relatorio_detalhado_{period_str['start']}_a_{period_str['end']}.xlsx"

        st.download_button(label="📥 Baixar Relatório Detalhado (.xlsx)", data=output.getvalue(), file_name=file_name_str, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
