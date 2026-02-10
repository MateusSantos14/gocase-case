import pandas as pd
from sqlalchemy import create_engine, text
import json
import os
import time
from datetime import datetime

# Carregar variáveis de ambiente manualmente se necessário (para execução local)
def carregar_env():
    arquivo_env = '.env'
    if os.path.exists(arquivo_env):
        with open(arquivo_env) as f:
            for linha in f:
                if linha.strip() and not linha.startswith('#'):
                    chave, valor = linha.strip().split('=', 1)
                    os.environ[chave] = valor

carregar_env()

# Detalhes da conexão com o banco de dados
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "gocase_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def obter_engine():
    tentativas = 10
    while tentativas > 0:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                return engine
        except Exception as e:
            print(f"Banco de dados não está pronto, tentando novamente em 5s... ({e})")
            time.sleep(5)
            tentativas -= 1
    raise Exception("Não foi possível conectar ao banco de dados")

def limpar_moeda(valor):
    if isinstance(valor, str):
        return float(valor.replace('.', '').replace(',', '.'))
    return valor

def analisar_datas(data_str):
    if not isinstance(data_str, str):
        return None
    
    mapa_meses = {
        "jan.": "Jan", "fev.": "Feb", "mar.": "Mar", "abr.": "Apr",
        "mai.": "May", "jun.": "Jun", "jul.": "Jul", "ago.": "Aug",
        "set.": "Sep", "out.": "Oct", "nov.": "Nov", "dez.": "Dec"
    }
    
    for pt, en in mapa_meses.items():
        if pt in data_str:
            data_str = data_str.replace(pt, en)
            break
            
    try:
        return pd.to_datetime(data_str, format="%d %b, %Y, %H:%M")
    except ValueError:
        return None

def configurar_banco(engine):
    with engine.connect() as conn:
        # Reiniciar esquema para garantir limpeza
        conn.execute(text("DROP TABLE IF EXISTS itens CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS pedidos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS suprimentos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS dados_brutos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS visoes_dashboard CASCADE;"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dados_brutos (
                id SERIAL PRIMARY KEY,
                arquivo_origem TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dados_brutos JSONB
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id_pedido TEXT PRIMARY KEY,
                cliente_ref TEXT,
                criado_em TIMESTAMP,
                status TEXT,
                valor_total NUMERIC,
                custo_frete NUMERIC,
                cidade_cliente TEXT,
                estado_cliente TEXT,
                cep_cliente TEXT,
                transportadora TEXT,
                contagem_itens INTEGER,
                peso_kg NUMERIC,
                
                -- Colunas de Engenharia de Recursos
                total_itens_preco NUMERIC,
                desconto_implicito NUMERIC,
                desconto_perc NUMERIC,
                mes_pedido INTEGER,
                ano_pedido INTEGER,
                dia_semana INTEGER
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS itens (
                id SERIAL PRIMARY KEY,
                id_pedido TEXT REFERENCES pedidos(id_pedido),
                id_produto TEXT,
                id_material TEXT,
                nome_material TEXT,
                categoria TEXT,
                preco NUMERIC,
                status TEXT,
                quantidade INTEGER DEFAULT 1
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS suprimentos (
                id_suprimento TEXT PRIMARY KEY,
                id_material TEXT,
                nome_material TEXT,
                quantidade INTEGER,
                tempo_entrega INTEGER,
                id_fabrica INTEGER,
                descontinuado BOOLEAN
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS visoes_dashboard (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                descricao_prompt TEXT,
                estrutura_json JSONB
            );
        """))
        conn.commit()

def carregar_dados_brutos(engine, df, arquivo_origem):
    # Substituir NaN por None para JSON válido
    df_limpo = df.astype(object).where(pd.notnull(df), None)
    registros = df_limpo.to_dict(orient='records')
    
    with engine.connect() as conn:
        for registro in registros:
            conn.execute(
                text("INSERT INTO dados_brutos (arquivo_origem, dados_brutos) VALUES (:origem, :dados)"),
                {"origem": arquivo_origem, "dados": json.dumps(registro, default=str)}
            )
        conn.commit()

def processar_pedidos(engine):
    print("Processando Pedidos...")
    df = pd.read_csv('dados/Pedidos.csv')

    carregar_dados_brutos(engine, df, 'Pedidos.csv')

    df_limpo = pd.DataFrame()
    df_limpo['id_pedido'] = df['id'].astype(str)
    df_limpo['cliente_ref'] = df['reference'].astype(str)
    
    df_limpo['criado_em'] = df['created_at'].apply(analisar_datas)
    
    df_limpo['status'] = df['order_state']
    df_limpo['valor_total'] = df['Valor de NF (R$)'].apply(limpar_moeda)
    df_limpo['custo_frete'] = df['Frete Cobrado do Cliente (R$)'].apply(limpar_moeda)
    df_limpo['cidade_cliente'] = df['Cidade']
    df_limpo['estado_cliente'] = df['Estado']
    df_limpo['cep_cliente'] = df['CEP'].astype(str)
    df_limpo['transportadora'] = df['Transportadora']
    df_limpo['contagem_itens'] = pd.to_numeric(df['Número de Itens no Pedido'], errors='coerce').fillna(0)
    df_limpo['peso_kg'] = df['Peso (kg)'].apply(limpar_moeda)

    df_limpo['mes_pedido'] = df_limpo['criado_em'].dt.month
    df_limpo['ano_pedido'] = df_limpo['criado_em'].dt.year
    df_limpo['dia_semana'] = df_limpo['criado_em'].dt.dayofweek

    return df_limpo

def processar_itens(engine):
    print("Processando Itens...")
    df = pd.read_csv('dados/Itens.csv')
    
    carregar_dados_brutos(engine, df, 'Itens.csv')

    df_limpo = pd.DataFrame()
    df_limpo['id_pedido'] = df['order_id'].astype(str)
    df_limpo['id_produto'] = df['product_id'].astype(str)
    df_limpo['id_material'] = df['material_id'].astype(str)
    df_limpo['nome_material'] = df['material_name']
    df_limpo['categoria'] = df['material_category']
    df_limpo['preco'] = df['price'].apply(limpar_moeda)
    df_limpo['status'] = df['aasm_state']
    
    return df_limpo

def processar_suprimentos(engine):
    print("Processando Suprimentos...")
    df = pd.read_csv('dados/Supply.csv')

    carregar_dados_brutos(engine, df, 'Supply.csv')

    df_limpo = pd.DataFrame()
    df_limpo['id_suprimento'] = df['supply_id'].astype(str)
    df_limpo['id_material'] = df['material_id'].astype(str)
    df_limpo['nome_material'] = df['material_name']
    df_limpo['quantidade'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
    df_limpo['tempo_entrega'] = pd.to_numeric(df['leadtime'], errors='coerce').fillna(0)
    df_limpo['id_fabrica'] = pd.to_numeric(df['factory_id'], errors='coerce').fillna(0)
    df_limpo['descontinuado'] = df['discontinued'].astype(bool)

    df_limpo.to_sql('suprimentos', engine, if_exists='append', index=False, method='multi', chunksize=1000)

    return df_limpo

def main():
    engine = obter_engine()
    configurar_banco(engine)

    df_pedidos = processar_pedidos(engine)
    df_itens = processar_itens(engine)
    processar_suprimentos(engine)

    # Engenharia de Recursos
    soma_itens_pedido = df_itens.groupby('id_pedido')['preco'].sum().reset_index()
    soma_itens_pedido.rename(columns={'preco': 'total_itens_preco'}, inplace=True)

    pedidos_final = pd.merge(df_pedidos, soma_itens_pedido, on='id_pedido', how='left')
    pedidos_final['total_itens_preco'] = pedidos_final['total_itens_preco'].fillna(0)

    pedidos_final['desconto_implicito'] = (pedidos_final['total_itens_preco'] + pedidos_final['custo_frete']) - pedidos_final['valor_total']
    pedidos_final['desconto_implicito'] = pedidos_final['desconto_implicito'].round(2)
    
    # Calcular porcentagem (evitar divisão por zero)
    # Base de cálculo: total_itens + frete (preço original cheio)
    pedidos_final['base_original'] = pedidos_final['total_itens_preco'] + pedidos_final['custo_frete']
    pedidos_final['desconto_perc'] = pedidos_final.apply(
        lambda x: (x['desconto_implicito'] / x['base_original'] * 100) if x['base_original'] > 0 else 0.0, 
        axis=1
    )
    pedidos_final['desconto_perc'] = pedidos_final['desconto_perc'].round(2)
    
    # Remover coluna temporária se quiser, ou manter. O to_sql vai reclamar se não estiver no schema?
    # O pd.to_sql com method multi cria as colunas se não existirem? Não, eu criei a tabela manualmente antes com CREATE TABLE.
    # Preciso adicionar desconto_perc no CREATE TABLE acima.
    pedidos_final.drop(columns=['base_original'], inplace=True)


    print("Carregando Pedidos no BD...")
    pedidos_final.to_sql('pedidos', engine, if_exists='append', index=False, method='multi', chunksize=1000)
    
    
    # Filtrar itens órfãos
    ids_pedidos_validos = set(pedidos_final['id_pedido'].astype(str))
    df_itens = df_itens[df_itens['id_pedido'].isin(ids_pedidos_validos)]
    
    if not df_itens.empty:
        print(f"Carregando {len(df_itens)} Itens válidos no BD...")
        df_itens.to_sql('itens', engine, if_exists='append', index=False, method='multi', chunksize=1000)
    else:
        print("AVISO: Nenhum item para carregar!")

    print("Pipeline Finalizado com Sucesso!")

if __name__ == "__main__":
    main()
