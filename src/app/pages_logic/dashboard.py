import streamlit as st
import servicos.banco as banco
from utils.ui_helpers import renderizar_visao

def render(params_globais):
    st.header("Dashboard - Visualização")
    visoes = banco.listar_visoes()
    
    if visoes is not None and not visoes.empty:
        opcoes = visoes['nome'].tolist()
        # Adicionar chave única para evitar conflitos de widget ID se renderizar novamente
        opcao_visao = st.selectbox("Selecione a Visão", opcoes, key="dash_select_visao")
        
        row_visao = visoes[visoes['nome'] == opcao_visao].iloc[0]
        renderizar_visao(row_visao['estrutura_json'], params_globais)
    else:
        st.info("Nenhuma visão disponível. Vá em 'Gerenciar Visões' para criar uma.")
