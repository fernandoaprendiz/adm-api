# shared_funcs.py (MÓDULO CENTRAL DE FUNÇÕES DE API)

import streamlit as st
import requests
import pandas as pd
import io
from typing import List, Dict, Optional, Any
from datetime import date, timedelta
from decimal import Decimal

# --- CONFIGURAÇÃO ---
API_BASE_URL = "https://setdoc-api-gateway-308638875599.southamerica-east1.run.app"

# --- FUNÇÕES DE AJUDA E ERRO ---
def handle_api_error(e: requests.exceptions.RequestException, action: str):
    st.error(f"Falha ao {action}.")
    if e.response is not None:
        try: st.error(f"Detalhe: {e.response.json().get('detail', e.response.text)}")
        except: st.error(f"Detalhe: {e.response.text}")

# --- FUNÇÕES DE API (COMPARTILHADAS) ---

# GERA UMA CHAVE DE ADMIN PARA SER USADA PELAS FUNÇÕES
def get_headers(api_key: str) -> Dict[str, str]:
    return {"x-api-key": api_key}

def check_admin_auth(api_key: str) -> bool:
    """Tenta autenticar no endpoint de admin."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=get_headers(api_key), timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 403: return False
        return False

# Funções de Contas e Usuários
@st.cache_data(ttl=30)
def get_all_accounts(api_key: str) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/", headers=get_headers(api_key)); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar contas"); return None

def create_new_account(name: str, cod_tri7: Optional[int], cidade: Optional[str], uf: Optional[str], api_key: str):
    payload = {"name": name}
    if cod_tri7: payload["cod_tri7"] = cod_tri7
    if cidade: payload["cidade"] = cidade
    if uf: payload["uf"] = uf
    try:
        response = requests.post(f"{API_BASE_URL}/admin/accounts/", headers=get_headers(api_key), json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar conta"); return None

@st.cache_data(ttl=30)
def get_users_for_account(account_id: int, api_key: str) -> Optional[List[Dict]]:
    try:
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/users/", headers=get_headers(api_key)); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar usuários"); return None

def create_new_user(full_name: str, email: str, password: str, account_id: int, api_key: str):
    payload = {"full_name": full_name, "email": email, "password": password, "account_id": account_id}
    try: 
        response = requests.post(f"{API_BASE_URL}/admin/users/", headers=get_headers(api_key), json=payload); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar usuário"); return None

def set_account_status(account_id: int, is_active: bool, api_key: str) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/status?active_status={is_active}", headers=get_headers(api_key)); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, f"mudar status da conta"); return False

def set_user_status(user_id: int, is_active: bool, api_key: str) -> bool:
    try:
        response = requests.put(f"{API_BASE_URL}/admin/users/{user_id}/status?active_status={is_active}", headers=get_headers(api_key)); response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, f"mudar status do usuário"); return False

def regenerate_api_key(user_id: int, api_key: str) -> Optional[str]:
    try:
        response = requests.post(f"{API_BASE_URL}/admin/users/{user_id}/regenerate-api-key", headers=get_headers(api_key)); response.raise_for_status()
        return response.json().get("api_key")
    except requests.exceptions.RequestException as e: handle_api_error(e, "regenerar chave de API"); return None

# Funções de Prompts e Permissões
@st.cache_data(ttl=60)
def get_all_prompts(api_key: str):
    try: response = requests.get(f"{API_BASE_URL}/admin/prompts/", headers=get_headers(api_key)); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar prompts"); return None

def create_new_prompt(name: str, text: str, api_key: str):
    try: response = requests.post(f"{API_BASE_URL}/admin/prompts/", headers=get_headers(api_key), json={"name": name, "prompt_text": text}); response.raise_for_status(); return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "criar prompt"); return None

def update_prompt_details(prompt_id: int, name: str, text: str, api_key: str):
    try: response = requests.put(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=get_headers(api_key), json={"name": name, "prompt_text": text}); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "atualizar prompt"); return False

def delete_prompt(prompt_id: int, api_key: str):
    try: response = requests.delete(f"{API_BASE_URL}/admin/prompts/{prompt_id}", headers=get_headers(api_key)); response.raise_for_status(); return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "deletar prompt"); return False

@st.cache_data(ttl=60)
def get_account_permissions(account_id: int, api_key: str):
    try: 
        response = requests.get(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=get_headers(api_key)); response.raise_for_status()
        return response.json().get("prompt_ids", [])
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar permissões"); return []

def sync_account_permissions(account_id: int, prompt_ids: List[int], api_key: str):
    try:
        response = requests.put(f"{API_BASE_URL}/admin/accounts/{account_id}/permissions", headers=get_headers(api_key), json={"prompt_ids": prompt_ids})
        response.raise_for_status()
        get_account_permissions.clear() # Limpa o cache após salvar
        return True
    except requests.exceptions.RequestException as e: handle_api_error(e, "salvar permissões"); return False

# Função de Faturamento
def get_master_billing_report(start_date: str, end_date: str, account_id: Optional[int], api_key: str):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id is not None: params["account_id"] = account_id
    try:
        response = requests.get(f"{API_BASE_URL}/billing/report/", headers=get_headers(api_key), params=params); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "gerar relatório"); return None

def get_detailed_billing_jobs(start_date: str, end_date: str, account_id: Optional[int], api_key: str):
    params = {"start_date": start_date, "end_date": end_date}
    if account_id is not None: params["account_id"] = account_id
    try:
        response = requests.get(f"{API_BASE_URL}/billing/detailed-report/", headers=get_headers(api_key), params=params); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e: handle_api_error(e, "buscar detalhe do relatório"); return None
