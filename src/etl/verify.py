import pandas as pd
from sqlalchemy import create_engine, text
import os

# Carregar variáveis de ambiente manualmente
def carregar_env():
    arquivo_env = '.env'
    if os.path.exists(arquivo_env):
        with open(arquivo_env) as f:
            for linha in f:
                if linha.strip() and not linha.startswith('#'):
                    chave, valor = linha.strip().split('=', 1)
                    os.environ[chave] = valor

carregar_env()

DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "gocase_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("--- Relatório de Verificação (PT-BR) ---")
            
            # Verificar Tabela de Dados Brutos
            resultado = conn.execute(text("SELECT COUNT(*) FROM dados_brutos")).scalar()
            print(f"Contagem Tabela Dados Brutos: {resultado}")
            
            # Verificar Pedidos
            resultado = conn.execute(text("SELECT COUNT(*) FROM pedidos")).scalar()
            print(f"Contagem Tabela Pedidos: {resultado}")
            
            # Verificar Itens
            resultado = conn.execute(text("SELECT COUNT(*) FROM itens")).scalar()
            print(f"Contagem Tabela Itens: {resultado}")
            
            # Verificar Suprimentos
            resultado = conn.execute(text("SELECT COUNT(*) FROM suprimentos")).scalar()
            print(f"Contagem Tabela Suprimentos: {resultado}")
            
            # Verificar Engenharia de Recursos
            print("\n--- Verificação de Engenharia de Recursos ---")
            resultado = conn.execute(text("SELECT id_pedido, valor_total, total_itens_preco, custo_frete, desconto_implicito FROM pedidos LIMIT 5")).fetchall()
            for row in resultado:
                print(f"Pedido: {row[0]}, Total: {row[1]}, Itens: {row[2]}, Frete: {row[3]}, Desconto: {row[4]}")
                
            print("\n--- Verificação de Datas ---")
            resultado = conn.execute(text("SELECT criado_em, mes_pedido, ano_pedido, dia_semana FROM pedidos LIMIT 5")).fetchall()
            for row in resultado:
                print(f"Data: {row[0]}, Mês: {row[1]}, Ano: {row[2]}, DiaSemana: {row[3]}")
                
    except Exception as e:
        print(f"Erro na verificação: {e}")

if __name__ == "__main__":
    main()
