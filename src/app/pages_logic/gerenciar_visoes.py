import streamlit as st
import json
import os
import requests
import subprocess
import servicos.banco as banco
from utils.ui_helpers import renderizar_visao

def render(params_globais):
    st.header("Central de Visões")
    
    tab_lista, tab_ia, tab_manual = st.tabs(["Minhas Visões", "Criar com IA", "Criar Manualmente"])
    
    # --- ABA 1: LISTAR / EDITAR / EXCLUIR ---
    with tab_lista:
        render_tab_lista(params_globais)

    # --- ABA 2: CRIAR COM IA ---
    with tab_ia:
        render_tab_ia(params_globais)

    # --- ABA 3: CRIAR MANUALMENTE ---
    with tab_manual:
        render_tab_manual(params_globais)

def render_tab_lista(params_globais):
    visoes = banco.listar_visoes()
    if visoes is not None and not visoes.empty:
        opcoes = {f"{row['id']} - {row['nome']}": row['id'] for index, row in visoes.iterrows()}
        # Key única para evitar conflito com Dashboard
        opcao_selecionada = st.selectbox("Selecione uma Visão para Gerenciar", list(opcoes.keys()), key="mgr_select_visao")
        
        id_selecionado = opcoes[opcao_selecionada]
        row_visao = visoes[visoes['id'] == id_selecionado].iloc[0]
        json_estrutura = row_visao['estrutura_json']
        
        # Ações
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.download_button("Exportar JSON", data=json.dumps(json_estrutura, indent=4, ensure_ascii=False), file_name=f"visao_{id_selecionado}.json", mime="application/json", key=f"dl_{id_selecionado}")
        with c2:
            if st.button("Excluir Visão", type="primary", key=f"del_{id_selecionado}"):
                banco.deletar_visao(id_selecionado)
                st.success("Deletado!")
                st.rerun()
        with c3:
            # Botão para testar envio n8n (Script Global)
            if st.button("Enviar p/ n8n (Script)", key=f"n8n_script_{id_selecionado}"):
                with st.spinner("Processando e enviando..."):
                    try:
                        # Extrair datas dos parâmetros globais
                        d_inicio = params_globais.get("data_inicio")
                        d_fim = params_globais.get("data_fim")
                        
                        cmd = ["python", "src/jobs/processar_visoes.py"]
                        
                        if d_inicio:
                            cmd.extend(["--start", str(d_inicio)])
                        if d_fim:
                            cmd.extend(["--end", str(d_fim)])
                            
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if res.returncode == 0:
                            st.success("Enviado com sucesso! Verifique o n8n.")
                            with st.expander("Logs do Envio"):
                                st.code(res.stdout)
                        else:
                            st.error("Erro ao executar script.")
                            st.code(res.stderr + "\n" + res.stdout)
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.divider()
        
        # Edição
        with st.expander("Editar Detalhes", expanded=False):
            novo_nome = st.text_input("Nome", value=row_visao['nome'], key=f"edit_nome_{id_selecionado}")
            novo_prompt = st.text_area("Prompt", value=row_visao['descricao_prompt'], key=f"edit_prompt_{id_selecionado}")
            json_str = st.text_area("JSON Estrutura", value=json.dumps(json_estrutura, indent=4, ensure_ascii=False), height=300, key=f"edit_json_{id_selecionado}")
            
            if st.button("Salvar Alterações", key=f"save_edit_{id_selecionado}"):
                try:
                    novo_json = json.loads(json_str)
                    banco.atualizar_visao(int(id_selecionado), novo_nome, novo_prompt, novo_json)
                    st.success("Atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        st.subheader("Pré-visualização da Visão Selecionada")
        imgs = renderizar_visao(json_estrutura, params_globais)

        # Botão envio granular (imagens na tela)
        if st.button("Enviar p/ n8n (Imagens na Tela)", key=f"send_imgs_{id_selecionado}"):
             if not imgs:
                 st.warning("Nenhum gráfico gerado para enviar.")
             else:
                 with st.spinner("Enviando imagens em lote..."):
                     WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'http://n8n-main:5678/webhook/relatorio')
                     
                     files_to_send = []
                     metadata_list = []
                     
                     for item in imgs:
                         item['buffer'].seek(0)
                         files_to_send.append(('files', (f"{item['titulo']}.png", item['buffer'], 'image/png')))
                         metadata_list.append({
                             'nome_visao': row_visao['nome'],
                             'titulo_grafico': item['titulo'],
                             'descricao': json_estrutura.get('descricao_prompt', ''),
                             'dados_raw': item.get('dados_raw')
                         })

                     try:
                         # Enviar metadados como JSON string
                         data_payload = {'metadata': json.dumps(metadata_list)}
                         
                         res = requests.post(WEBHOOK_URL, files=files_to_send, data=data_payload, timeout=30)
                         
                         if res.status_code == 200:
                             st.success(f"Enviado com sucesso! Código: {res.status_code}")
                             with st.expander("Resposta do Servidor"):
                                 st.write(res.text)
                         else:
                             st.error(f"Falha ao enviar lote: {res.status_code}")
                             st.error(res.text)
                     except Exception as e:
                         st.error(f"Erro ao enviar solicitação: {e}")

    else:
        st.info("Nenhuma visão criada. Use as abas ao lado para criar.")

def render_tab_ia(params_globais):
    st.subheader("Criar Nova Visão com IA")
    prompt = st.text_area("Descreva o que você quer ver", placeholder="Ex: Vendas por estado...", key="ia_prompt")
    
    if st.button("Gerar Visão (IA)", key="btn_gerar_ia"):
        if 'ia_service' in st.session_state:
            with st.spinner("Gerando..."):
                resultado = st.session_state['ia_service'].gerar_visao_sql(prompt)
                if "erro" in resultado:
                    st.error(resultado["erro"])
                else:
                    st.session_state['visao_gerada'] = {"prompt": prompt, "resultado": resultado}
        else:
            st.error("Serviço IA não inicializado. Recarregue a página.")
    
    if 'visao_gerada' in st.session_state:
        visao = st.session_state['visao_gerada']['resultado']
        st.json(visao)
        renderizar_visao(visao, params_globais)
        if st.button("Salvar Visão (IA)", key="btn_salvar_ia"):
            banco.salvar_visao(visao.get("nome"), st.session_state['visao_gerada']['prompt'], visao)
            st.success("Salva!")
            del st.session_state['visao_gerada']
            st.rerun()

def render_tab_manual(params_globais):
    st.subheader("Criar Manualmente")
    nome_visao = st.text_input("Nome da Visão Nova", key="man_nome")
    descricao = st.text_area("Descrição (opcional) Manual", key="man_desc")
    
    if 'componentes_manuais' not in st.session_state:
        st.session_state['componentes_manuais'] = []

    with st.expander("Adicionar Componente"):
        tipo_c = st.selectbox("Tipo", ["indicador", "grafico_barra", "grafico_linha", "tabela"], key="man_tipo")
        titulo_c = st.text_input("Título", key="man_titulo")
        sql_c = st.text_area("SQL", key="man_sql")
        eixo_x = st.text_input("Eixo X", key="man_x")
        eixo_y = st.text_input("Eixo Y", key="man_y")
        
        if st.button("Add Componente", key="man_add"):
            comp = {"tipo": tipo_c, "titulo": titulo_c, "sql": sql_c, "eixo_x": eixo_x, "eixo_y": eixo_y}
            st.session_state['componentes_manuais'].append(comp)
            st.success("Adicionado!")
    
    if st.session_state['componentes_manuais']:
        st.write("Componentes Adicionados:")
        st.write(st.session_state['componentes_manuais'])
    
    if st.button("Salvar Visão Manual", key="man_salvar"):
        if not nome_visao or not st.session_state['componentes_manuais']:
            st.error("Preencha nome e adicione componentes.")
        else:
            est = {"nome": nome_visao, "componentes": st.session_state['componentes_manuais']}
            banco.salvar_visao(nome_visao, descricao, est)
            st.success("Salva!")
            st.session_state['componentes_manuais'] = []
            st.rerun()
