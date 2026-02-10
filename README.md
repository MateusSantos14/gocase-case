# Analytics - Dashboard Inteligente

Este projeto é uma solução completa de Engenharia de Dados e Business Intelligence para análise de pedidos da GoCase. Ele processa dados brutos (CSV), carrega em um Data Warehouse PostgreSQL e disponibiliza um Dashboard interativo com capacidades de IA Generativa.

---

## Funcionalidades Principais

### 1. Pipeline de Dados (ETL)
- **Ingestão**: Lê arquivos `Orders.csv`, `Items.csv` e `Supply.csv`.
- **Tratamento**: Limpeza de dados, conversão de tipos e cálculo de colunas derivadas (ex: `mes_pedido`, `ano_pedido`).
- **Carga**: Armazena em um banco PostgreSQL estruturado (`pedidos`, `itens`, `suprimentos`).

### 2. Dashboard Interativo
- **Visualização**: Gráficos dinâmicos (linhas, barras, indicadores) usando Plotly.
- **Filtros Globais**: Data, Status e Remoção de Outliers.
- **Abas**:
    - **Dashboard**: Visualização executiva.
    - **Gerenciar Visões**: CRUD completo para criar, editar e excluir visões.
    - **Playground SQL**: Ambiente para testar queries diretamente no banco.
    - **Qualidade de Dados**: Monitoramento de integridade e outliers.

### 3. Geração de Insights com IA (Gemini)
- Crie visões complexas apenas descrevendo o que você quer ver em linguagem natural (ex: *"Mostre o total de vendas por mês"*).
- A IA gera a consulta SQL e configura o gráfico automaticamente.

---

## Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados.
- Chave de API do Google Gemini (para funcionalidades de IA).

### Passo a Passo

1. **Configurar Ambiente**:
   Crie um arquivo `.env` na raiz com sua chave de API:
   ```env
   GOOGLE_API_KEY=sua_chave_aqui
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   POSTGRES_DB=gocase_db
   POSTGRES_PORT=5433
   DB_HOST=localhost
   ```

2. **Iniciar Serviços**:
   Utilize o script facilitador para subir o banco e o dashboard:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   *Isso irá subir os containers Docker e rodar o pipeline ETL automaticamente.*

### 1. Acesso ao Dashboard

Após iniciar os serviços, acesse:
- **Localmente**: [http://localhost:8501](http://localhost:8501)
- **Via Túnel (Ngrok)**: Verifique a URL gerada no log do container `ngrok-tunnel` ou acesse conforme configurado no seu painel.

> **Nota**: O Nginx redireciona `/` para o N8N e `/dashboard/` para a aplicação.

### 2. Credenciais
As credenciais de acesso padrão estão configuradas no arquivo `SECRETS.md` (não versionado) ou no `.env`.
Consulte o administrador do sistema para obter acesso.

---

## Perguntas de Negócio (Análises Chave)

O dashboard foi desenhado para responder às seguintes perguntas estratégicas:

### 1. Vendas & Conversão
*   **Distribuição Temporal**: Como os pedidos evoluem ao longo do tempo? Existem picos sazonais ou diários?
*   **Impacto de Descontos**: Existe correlação entre a porcentagem de desconto aplicada e o aumento no volume de vendas?
*   **Produtos & Categorias**: Quais categorias ou itens específicos trazem maior retorno financeiro (Faturamento)?

---

## Prompt Sugerido para IA

Para criar uma visão que responda a todas essas perguntas de uma vez, vá na aba **"Gerenciar Visões" > "Criar com IA"** e cole o seguinte prompt:

> Crie um dashboard executivo completo com 4 componentes:
> 1. Um **Gráfico de Linha** mostrando a evolução diária do total de vendas (`SUM(valor_total)`) ao longo do tempo (eixo X: dia de `criado_em`, eixo Y: vendas). Título: "Evolução Diária de Vendas".
> 2. Um **Gráfico de Barras** mostrando o Faturamento Total por Categoria de Item (junte `pedidos` com `itens`). Título: "Faturamento por Categoria".
> 3. Um **Gráfico de Dispersão (Scatter)** ou Linha comparando a Média de Desconto Implícito vs Volume de Vendas Diário. Título: "Correlação Desconto x Volume".
> 4. Uma **Tabela** com os Top 5 Produtos mais vendidos (por receita). Título: "Top 5 Produtos".

---

### 4. Automação com N8N (Gemini Vision + E-mail)
- **Análise Visual**: O N8N recebe gráficos do dashboard, usa o Gemini Vision para analisá-los e envia um relatório por e-mail.
- **Integração Simples**: Todo o fluxo é baseado em webhooks e transferência de imagem via Base64.
- **Documentação**: Veja o guia completo em [docs/N8N_INTEGRATION.md](docs/N8N_INTEGRATION.md).

---

## Estrutura do Projeto

```
gocase/
├── dados/               # Arquivos CSV brutos
├── docs/                # Documentação (Manuais e Tutoriais)
├── src/
│   ├── app/             # Aplicação Streamlit
│   │   ├── main.py      # Código principal do Dashboard
│   │   ├── servicos/    # Módulos de Banco e IA
│   ├── etl/             # Scripts de ETL (Extração, Transformação, Carga)
├── docker-compose.yml   # Orquestração dos containers
├── run.sh               # Script de automação
└── README.md            # Documentação
```
