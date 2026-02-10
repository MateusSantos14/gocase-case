import streamlit as st
import pandas as pd
import servicos.banco as banco
import servicos.ia as ia

# Importar páginas modulares
import pages_logic.dashboard as dashboard_page
import pages_logic.gerenciar_visoes as manager_page
import pages_logic.explorador as explorer_page

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analytics Dashboard", layout="wide")
st.title("Analytics - Dashboard Inteligente")

# --- SERVIÇOS ---
if 'ia_service' not in st.session_state:
    st.session_state['ia_service'] = ia.ServicoIA()

# --- SIDEBAR E FILTROS ---
st.sidebar.header("Filtros Globais")

# Carregar datas dinâmicas (Cache simples via banco)
df_datas = banco.executar_consulta("SELECT MIN(criado_em) as inicio, MAX(criado_em) as fim FROM pedidos")
data_min = pd.to_datetime("2025-01-01")
data_max = pd.to_datetime("2025-12-31")

if df_datas is not None and not df_datas.empty:
    data_min = pd.to_datetime(df_datas.iloc[0]['inicio'])
    data_max = pd.to_datetime(df_datas.iloc[0]['fim'])

data_inicio = st.sidebar.date_input("Data Início", data_min, min_value=data_min, max_value=data_max)
data_fim = st.sidebar.date_input("Data Fim", data_max, min_value=data_min, max_value=data_max)

# Objeto de params globais para passar às páginas
params_globais = {"data_inicio": data_inicio, "data_fim": data_fim}

# Menu de Navegação Limpo
menu = st.sidebar.radio("Navegação", ["Dashboard", "Gerenciar Visões", "Explorador de Dados"])

# --- ROTEAMENTO ---
if menu == "Dashboard":
    dashboard_page.render(params_globais)

elif menu == "Gerenciar Visões":
    manager_page.render(params_globais)

elif menu == "Explorador de Dados":
    explorer_page.render(params_globais)
