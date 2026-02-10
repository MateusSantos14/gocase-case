import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text

# Configuração do Banco (Assumindo Docker ou Local via env)
# Em produção real, usaria variáveis de ambiente melhor geridas
DB_USER = os.getenv('POSTGRES_USER', 'user')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5433') # Default local
DB_NAME = os.getenv('POSTGRES_DB', 'gocase_db')

def get_connection():
    # Ajuste para rodar dentro do container ou fora
    # Se rodar via n8n (que pode estar em outro container), a conexão pode variar
    # Mas assumindo execução local/teste por enquanto
    url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def gerar_grafico_vendas_diarias():
    engine = get_connection()
    query = """
    SELECT DATE(criado_em) as dia, SUM(valor_total) as total_vendas
    FROM pedidos
    GROUP BY dia
    ORDER BY dia
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("Sem dados para gerar gráfico.")
        return

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='dia', y='total_vendas', marker='o')
    plt.title('Evolução Diária de Vendas')
    plt.xlabel('Data')
    plt.ylabel('Vendas (R$)')
    plt.grid(True)
    
    caminho = "relatorios/vendas_diarias.png"
    plt.savefig(caminho)
    print(f"Gráfico salvo em: {caminho}")

if __name__ == "__main__":
    gerar_grafico_vendas_diarias()
