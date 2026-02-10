import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text
from io import BytesIO
import argparse
from datetime import datetime, timedelta

# Configuração do Banco
DB_USER = os.getenv('POSTGRES_USER', 'user')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'password')
DB_NAME = os.getenv('POSTGRES_DB', 'gocase_db')

# Detecção de Ambiente (Docker vs Local)
if os.getenv('IS_DOCKER') == 'true':
    DB_HOST = 'db'
    DB_PORT = '5432'
else:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('POSTGRES_PORT', '5432')

# Webhook do N8N
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

def get_connection():
    url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def processar_visoes(data_inicio=None, data_fim=None):
    engine = get_connection()
    
    # 0. Definir Datas Padrão se não informadas
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not data_fim:
        data_fim = datetime.now().strftime('%Y-%m-%d')

    print(f"Usando período: {data_inicio} até {data_fim}")
    
    params = {
        "data_inicio": data_inicio, 
        "data_inicio_datetime": data_inicio, # Para compatibilidade se usar datetime
        "data_fim": data_fim,
        "data_fim_datetime": data_fim
    }

    # 1. Buscar todas as visões
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, nome, estrutura_json FROM visoes_dashboard"))
            visoes = result.fetchall()
    except Exception as e:
        print(f"Erro ao conectar banco: {e}")
        return

    print(f"Encontradas {len(visoes)} visões para processar.")

    # Otimização: Reutilizar conexão TCP
    session = requests.Session()
    
    files_to_send = []
    metadata_list = []

    for visao in visoes:
        id_visao, nome, json_raw = visao
        print(f"Processando: {nome}...")
        
        # O JSON pode vir como string ou dict dependendo do driver
        if isinstance(json_raw, str):
            estrutura = json.loads(json_raw)
        else:
            estrutura = json_raw
            
        componentes = estrutura.get('componentes', [])
        
        for comp in componentes:
            titulo = comp.get('titulo', 'Sem Título')
            sql = comp.get('sql')
            tipo = comp.get('tipo')
            
            if not sql or tipo not in ['grafico_barra', 'grafico_linha', 'grafico_combinado']:
                continue

            # 2. Executar Query
            try:
                # Importante: Envolver SQL em text() e passar params
                df = pd.read_sql(text(sql), engine, params=params)
            except Exception as e:
                print(f"Erro na query da visão {nome}: {e}")
                continue
                
            if df.empty:
                print(f"Sem dados para {titulo}")
                continue

            # 3. Gerar Gráfico
            try:
                plt.figure(figsize=(10, 6))
                
                eixo_x = comp.get('eixo_x')
                eixo_y = comp.get('eixo_y')
                eixo_y2 = comp.get('eixo_y2')
                
                if not (eixo_x and eixo_y and eixo_x in df.columns and eixo_y in df.columns):
                     print(f"Colunas inválidas para {titulo} (Esperado: {eixo_x}, {eixo_y}) - Colunas: {df.columns.tolist()}")
                     plt.close()
                     continue

                if tipo == 'grafico_barra':
                    sns.barplot(data=df, x=eixo_x, y=eixo_y)
                elif tipo == 'grafico_linha':
                    sns.lineplot(data=df, x=eixo_x, y=eixo_y, marker='o')
                elif tipo == 'grafico_combinado' and eixo_y2 and eixo_y2 in df.columns:
                    fig, ax1 = plt.subplots(figsize=(10,6))
                    sns.barplot(data=df, x=eixo_x, y=eixo_y, ax=ax1, color='b', alpha=0.6)
                    ax2 = ax1.twinx()
                    sns.lineplot(data=df, x=eixo_x, y=eixo_y2, ax=ax2, color='r', marker='o')
                    ax1.set_ylabel(eixo_y, color='b')
                    ax2.set_ylabel(eixo_y2, color='r')
                
                plt.title(f"{nome} - {titulo}")
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # 4. Salvar em Buffer (Memória)
                buf = BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()
                
                # Adicionar à lista de envio
                files_to_send.append(('files', (f"{nome}_{titulo}.png", buf, 'image/png')))
                metadata_list.append({
                    'nome_visao': nome,
                    'titulo_grafico': titulo,
                    'descricao': estrutura.get('descricao_prompt', '')
                })

            except Exception as e:
                print(f"Erro ao processar {titulo}: {e}")
                plt.close()

    # 5. Enviar TUDO para N8N (Batch)
    if files_to_send and WEBHOOK_URL:
        print(f"Enviando {len(files_to_send)} gráficos em lote para N8N...")
        try:
            # Enviar metadados como JSON string
            data_payload = {'metadata': json.dumps(metadata_list)}
            
            response = session.post(WEBHOOK_URL, files=files_to_send, data=data_payload, timeout=30)
            print(f"Status do Envio em Lote: {response.status_code}")
            if response.status_code != 200:
                print(f"Erro no envio: {response.text}")
        except Exception as e:
            print(f"Erro ao enviar request: {e}")
    elif not WEBHOOK_URL:
        print("URL do Webhook não configurada. Simulando envio...")
    else:
        print("Nenhum gráfico gerado para envio.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Processar visões e enviar relatórios.')
    parser.add_argument('--start', type=str, help='Data de início (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='Data de fim (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    processar_visoes(args.start, args.end)
