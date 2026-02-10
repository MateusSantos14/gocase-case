#!/bin/bash
set -e

# Carregar variáveis de ambiente
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "--- Iniciando Pipeline de Dados GoCase (V2 - PT-BR) ---"

# Verificar Dependências
if ! command -v docker-compose &> /dev/null; then
  echo "Erro: docker-compose não está instalado."
  exit 1
fi

if ! command -v python3 &> /dev/null; then
  echo "Erro: python3 não está instalado."
  exit 1
fi

# Modo Debug (Apenas Dashboard)
if [ "$1" == "--debug" ]; then
    echo "🐛 Iniciando Modo Debug (Apenas Dashboard)..."
    echo "⚠️ O ETL NÃO será executado. Dados podem estar desatualizados."
    echo "🔄 Reiniciando containers para garantir limpeza..."
    
    docker-compose down

    # Iniciar os serviços essenciais: db, n8n (para webhook) e streamlit
    # Nome do serviço no yaml é 'n8n', o container que é 'n8n-main'
    docker-compose up -d db n8n streamlit tunnel
    
    echo "✅ Dashboard: http://localhost:8501"
    echo "📝 Logs do Streamlit:"
    docker logs -f gocase-streamlit-1
    exit 0
fi

echo "🚀 Iniciando Pipeline Completo (ETL + Dashboard)..."
docker-compose down # Limpar execução anterior
docker-compose up -d

# Aguardar Banco de Dados
echo "Aguardando inicialização do Banco de Dados..."
sleep 10 # Docker check já faz isso, mas sleep extra ajuda na primeira vez

# Instalar Dependências Locais (ETL)
echo "Instalando Dependências Python (ETL)..."
pip install -r src/requirements_app.txt > /dev/null

# Executar ETL
echo "Executando Pipeline ETL..."
python3 src/etl/pipeline.py

echo "--- Pipeline Finalizado ---"
echo "Acesse o Dashboard em: http://localhost:8501"
