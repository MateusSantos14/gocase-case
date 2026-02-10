# 📊 GoCase Analytics - Roteiro de Apresentação

Este documento serve como guia para os slides da apresentação do projeto.

---

## **Slide 1: Visão Geral e Arquitetura**
*   **Titulo**: GoCase Analytics - Inteligência de Dados
*   **Objetivo**: Transformar dados brutos de pedidos e suprimentos em insights estratégicos.
*   **Arquitetura (Tech Stack)**:
    *   **ETL**: Python (Pandas) + Docker.
    *   **Armazenamento**: PostgreSQL 15 (Data Warehouse).
    *   **Visualização**: Streamlit + Plotly.
    *   **Inteligência**: Google Gemini AI (Geração de SQL).

---

## **Slide 2: Pipeline de Dados (ETL)**
*   **Extração (Extract)**:
    *   Leitura automatizada de arquivos CSV (`Orders.csv`, `Items.csv`, `Supply.csv`).
    *   Ingestão inicial em tabela `vision` (Raw Data / JSONB) para auditoria.
*   **Transformação (Transform)**:
    *   **Limpeza**: Conversão de datas, remoção de duplicatas, tratamento de nulos.
    *   **Enriquecimento**: Criação de colunas temporais (`mes_pedido`, `dia_semana`, `ano`).
    *   **Cálculos de Negócio**: `valor_total` corrigido, `desconto_implicito` calculado.
*   **Carga (Load)**:
    *   Inserção em modelo relacional normalizado: tabelas `pedidos`, `itens`, `suprimentos`.

---

## **Slide 3: Modelagem de Dados (Banco)**
*   **Estrutura Relacional**:
    *   **`pedidos` (Fato Central)**: Dados consolidados da venda (Valor, Cliente, Data, Status).
    *   **`itens` (Dimensão Produto)**: Detalhes SKU, categorias e preços unitários.
    *   **`suprimentos` (Dimensão Estoque)**: Controle de materiais e tempo de entrega.
*   **Benefícios**:
    *   Queries rápidas e otimizadas.
    *   Integridade referencial entre vendas e produtos.

---

## **Slide 4: O Dashboard Inteligente**
*   **Funcionalidades Chave**:
    1.  **Visão Executiva**: Gráficos interativos com filtros globais de data e status.
    2.  **Qualidade de Dados**: Aba dedicada para monitorar saúde dos dados (Outliers, Valores Negativos).
    3.  **Remoção de Ruído**: Filtro inteligente de Outliers (Top 5%) para "limpar" a visualização.
    4.  **Playground SQL**: Para validação técnica rápida.

---

## **Slide 5: O Diferencial - IA Generativa**
*   **"Converse com seus Dados"**:
    *   Integração com **Google Gemini**.
    *   Usuário descreve o que quer ver em português (ex: *"Vendas por estado"*).
    *   IA gera o SQL complexo e escolhe o melhor gráfico automaticamente.
    *   Suporte a gráficos avançados (Eixo Duplo: Vendas vs Desconto).
*   **Gestão de Visões (CRUD)**:
    *   Capacidade de Salvar, Editar e Exportar (JSON) as visões geradas pela IA.

---

---

## **Slide 6: Próximos Passos (Futuro - N8N & Slack)**
*   **Automação de Alertas**:
    *   **Ferramenta**: n8n (Workflow Automation).
    *   **Fluxo**: Banco de Dados -> Query Diária (ex: "Vendas < Meta") -> N8N -> Slack.
    *   **Visualização Estática**: Uso de **Matplotlib/Seaborn** para gerar imagens estáticas (PNG) e enviar no chat, já que Plotly requer interatividade (browser).
    *   **Benefício**: Tomada de decisão proativa sem precisar abrir o dashboard.

