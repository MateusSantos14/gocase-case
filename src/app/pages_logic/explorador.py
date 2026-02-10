import streamlit as st
import servicos.banco as banco

def render(params_globais):
    st.header("Explorador de Tabelas")
    
    # Listar tabelas permitidas
    tabelas = ["pedidos", "itens", "suprimentos"]
    tabela_sel = st.selectbox("Selecione a Tabela", tabelas, key="exp_select_tabela")
    
    if tabela_sel:
        # Consulta simples com limit
        limit = st.slider("Quantidade de linhas", 10, 1000, 50, key="exp_limit")
        df_exploracao = banco.executar_consulta(f"SELECT * FROM {tabela_sel} LIMIT {limit}")
        
        if df_exploracao is not None:
            st.dataframe(df_exploracao, use_container_width=True)
            st.caption(f"Mostrando as primeiras {limit} linhas de '{tabela_sel}'")
        else:
            st.error("Erro ao carregar tabela.")

    st.divider()
    st.subheader("Playground SQL (Teste de Queries)")
    st.info("Use este espaço para testar por que seus gráficos podem estar vindo vazios.")
    
    query_debug = st.text_area("Digite sua consulta SQL (Apenas LEITURA):", height=150, placeholder="SELECT desconto_perc, count(*) FROM pedidos GROUP BY desconto_perc", key="exp_query_debug")
    
    if st.button("Executar Query Manual", key="exp_btn_executar"):
        if query_debug.strip():
            with st.spinner("Executando..."):
                df_res = banco.executar_consulta(query_debug)
                if df_res is not None:
                    st.dataframe(df_res, use_container_width=True)
                    st.success(f"{len(df_res)} linhas retornadas.")
                else:
                    st.error("Erro na consulta. Verifique a sintaxe ou log do terminal.")
        else:
            st.warning("Digite uma query primeiro.")
