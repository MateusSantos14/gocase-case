import streamlit as st
import pandas as pd
import servicos.banco as banco
import servicos.visualizacao as visuais


@st.cache_data(ttl=300, show_spinner=False)
def consultar_com_cache(sql, params):
    return banco.executar_consulta(sql, params)


def filtrar_dataframe(df, data_inicio, data_fim):
    """
    Filtra um DataFrame por colunas de data/criado_em.
    """
    if df is None or df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # Filtro de Data
    # Tenta encontrar colunas de data
    for col in df_filtrado.columns:
        if 'data' in col.lower() or 'criado_em' in col.lower() or 'dia' in col.lower():
            try:
                # Converte para datetime se não for
                if not pd.api.types.is_datetime64_any_dtype(df_filtrado[col]):
                    df_filtrado[col] = pd.to_datetime(df_filtrado[col], errors='coerce')
                
                # Aplica o filtro
                if data_inicio and data_fim:
                    df_filtrado = df_filtrado[
                        (df_filtrado[col].dt.date >= data_inicio) & 
                        (df_filtrado[col].dt.date <= data_fim)
                    ]
            except Exception:
                pass # Se falhar conversão, ignora coluna
                    
    return df_filtrado


def renderizar_visao(json_visao, params_comb):
    """
    Renderiza os componentes de uma visão (Gráficos, Indicadores).
    Retorna lista de imagens geradas (buffer) para envio.
    """
    st.subheader(json_visao.get("nome", "Visão sem nome"))
    componentes = json_visao.get("componentes", [])
    
    # Armazenar imagens geradas para envio
    imagens_para_envio = []
    
    # Layout em Grid (2 colunas)
    for i, comp in enumerate(componentes):
        # Abre uma nova linha de colunas a cada par de componentes
        if i % 2 == 0:
            cols = st.columns(2)
        
        # Seleciona a coluna atual (0 ou 1)
        with cols[i % 2]:
            tipo = comp.get("tipo")
            titulo = comp.get("titulo")
            sql = comp.get("sql")
            
            st.markdown(f"**{titulo}**")
            
            if sql:
                # Filtragem de segurança
                try:
                    df = consultar_com_cache(sql, params_comb)
                    d_inicio = params_comb.get("data_inicio")
                    d_fim = params_comb.get("data_fim")
                    df = filtrar_dataframe(df, d_inicio, d_fim)
                except Exception as e:
                    st.error(f"Erro na query: {e}")
                    df = None
                
                if df is not None and not df.empty:
                    if tipo == "indicador":
                        val = df.iloc[0, 0]
                        if isinstance(val, (int, float)):
                            st.metric(label="Valor", value=f"{val:,.2f}")
                        else:
                            st.metric(label="Valor", value=str(val))
                            
                    elif tipo == "tabela":
                        st.dataframe(df, use_container_width=True)
                        buf_tab, erro_tab = visuais.gerar_tabela_imagem(df, titulo)
                        
                        item_envio = {
                            "titulo": f"{titulo} (Tabela)",
                            "buffer": buf_tab if buf_tab else None,
                            "dados_raw": df.to_dict(orient='records')
                        }
                        imagens_para_envio.append(item_envio)

                    elif tipo in ["grafico_barra", "grafico_linha", "grafico_combinado"]:
                        eixo_x = comp.get("eixo_x")
                        eixo_y = comp.get("eixo_y")
                        eixo_y2 = comp.get("eixo_y2")
                        
                        buf, erro = visuais.gerar_grafico(df, tipo, titulo, eixo_x, eixo_y, eixo_y2)
                        
                        if buf:
                            st.image(buf, use_container_width=True)
                            imagens_para_envio.append({
                                "titulo": titulo,
                                "buffer": buf,
                                "dados_raw": df.to_dict(orient='records')
                            })
                            buf.seek(0)
                        else:
                            st.error(f"Erro visual: {erro}")
                else:
                    st.warning("Sem dados.")
            else:
                st.error("SQL não definido.")
            
            st.markdown("---")
    
    return imagens_para_envio
