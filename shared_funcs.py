# shared_funcs.py (MÓDULO CENTRAL DE FUNÇÕES DE API E AJUDA)

import streamlit as st
import requests
import pandas as pd
import io
from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

# --- FUNÇÕES DE AJUDA ---
def handle_api_error(e: requests.exceptions.RequestException, action: str):
    """Função centralizada para lidar com erros de API."""
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try: st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except: st.error(f"Detalhe: {e.response.text}")

# --- FUNÇÕES DE API (COMPARTILHADAS) ---

# Função de autenticação não precisa de cache
def check_admin_auth(api_key: str) -> bool:
    """Tenta autenticar no endpoint de admin."""
    headers = {"x-api-key": api_key}
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 403: return False
        handle_api_error(e, "conectar e validar chave")
        return False

@st.cache_data(ttl=30)
def get_all_accounts(api_key: str) -> Optional[List[Dict]]:
    """Função que retorna a lista de contas."""
    headers = {"x-api-key": api_key}
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=headers); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None

# ... (Todas as outras funções de API como get_users_for_account, create_new_user, 
# set_account_status, regenerate_api_key, get_all_prompts, etc. devem ser colocadas aqui) ...

# Funções de API de Gestão (Exemplo, todas as suas funções devem vir aqui)
@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, api_key: str) -> Optional[List[Dict]]:
    headers = {"x-api-key": api_key}
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=headers); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None

def set_account_status(account_id: int, is_active: bool, api_key: str) -> bool:
    headers = {"x-api-key": api_key}
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=headers); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, f"mudar status da conta"); return False

# OBS: Para as próximas funções (como get_all_prompts), garanta que você altere
# a assinatura para que ela receba a api_key como argumento (ex: def func(..., api_key: str)).
# E remova o parâmetro 'headers' das funções, pois ele será criado dentro de cada uma.