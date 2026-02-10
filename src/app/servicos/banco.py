import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Se estiver rodando no Docker (via docker-compose que injeta IS_DOCKER=true),
# forçamos as credenciais internas, ignorando o .env montado que aponta para localhost
if os.getenv("IS_DOCKER") == "true":
    DB_HOST = "db"
    DB_PORT = "5432"
else:
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_NAME = os.getenv("POSTGRES_DB", "gocase_db")

# Ajuste para conexão correta no Docker vs Local
# Se estiver rodando no Docker, o DB_HOST deve ser 'db' e a porta 5432 (padrao interna)
# Se o .env diz 5433 (externa), o Docker Compose sobrescreve POSTGRES_PORT=5432 para o serviço.
# A lógica acima com load_dotenv() garante que o Docker vença.

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

_engine = None

def obter_conexao():
    global _engine
    if _engine is None:
        try:
            print(f"DEBUG: Conectando em {DB_HOST}:{DB_PORT} db={DB_NAME}")
            _engine = create_engine(DATABASE_URL)
        except Exception as e:
            print(f"Erro ao criar engine: {e}")
            return None
    return _engine

def executar_consulta(sql, params=None):
    # SEGURANÇA: Validar se é apenas leitura
    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        print(f"BLOQUEIO DE SEGURANÇA: Query tentou executar comando não permitido: {sql[:50]}...")
        return None

    engine = obter_conexao()
    if not engine:
        return None
    try:
        # Wrap em text() para evitar problemas com % (percentagem) sendo interpretado como placeholder
        # e para compatibilidade com SQLAlchemy 2.0+
        return pd.read_sql(text(sql), engine, params=params)
    except Exception as e:
        print(f"Erro SQL: {e}")
        return None

def salvar_visao(nome, prompt, estrutura_json):
    engine = obter_conexao()
    import json
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO visoes_dashboard (nome, descricao_prompt, estrutura_json) VALUES (:nome, :prompt, :json)"),
            {"nome": nome, "prompt": prompt, "json": json.dumps(estrutura_json)}
        )
        conn.commit()

def listar_visoes():
    sql = "SELECT id, nome, descricao_prompt, estrutura_json FROM visoes_dashboard ORDER BY id DESC"
    return executar_consulta(sql)

def atualizar_visao(id_visao, nome, prompt, estrutura_json):
    engine = obter_conexao()
    import json
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE visoes_dashboard SET nome = :nome, descricao_prompt = :prompt, estrutura_json = :json WHERE id = :id"),
            {"nome": nome, "prompt": prompt, "json": json.dumps(estrutura_json), "id": id_visao}
        )
        conn.commit()

def deletar_visao(id_visao):
    engine = obter_conexao()
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM visoes_dashboard WHERE id = :id"),
            {"id": id_visao}
        )
        conn.commit()


