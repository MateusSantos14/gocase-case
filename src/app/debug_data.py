import servicos.banco as banco
import pandas as pd

print("--- DIAGNOSTICO DE DADOS ---")

# 1. Verificar Tipos das Colunas
print("\n1. Tipos das Colunas em 'pedidos':")
try:
    df_types = banco.executar_consulta("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'pedidos';")
    print(df_types)
except Exception as e:
    print(f"Erro: {e}")

# 2. Verificar valores únicos de mes_pedido
print("\n2. Amostra de 'mes_pedido':")
try:
    df_mes = banco.executar_consulta("SELECT mes_pedido, COUNT(*) as qtd FROM pedidos GROUP BY mes_pedido ORDER BY mes_pedido;")
    print(df_mes)
except Exception as e:
    print(f"Erro: {e}")

# 3. Estatísticas de desconto_implicito e Data Range
print("\n3. Estatísticas e Datas:")
try:
    df_desc = banco.executar_consulta("SELECT MIN(desconto_implicito) as min_desc, MAX(desconto_implicito) as max_desc, MIN(valor_total) as min_val, MIN(criado_em) as inicio, MAX(criado_em) as fim FROM pedidos;")
    print(df_desc)
except Exception as e:
    print(f"Erro: {e}")
