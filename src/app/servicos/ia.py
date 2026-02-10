import os
from google import genai
import json

class ServicoIA:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_id = os.getenv("MODEL_NAME")
            self.ativo = True
        else:
            self.ativo = False
            print("AVISO: GOOGLE_API_KEY não encontrada. Funcionalidades de IA desativadas.")

    def gerar_visao_sql(self, prompt_usuario):
        if not self.ativo:
            return {
                "erro": "Chave de API não configurada. Adicione GOOGLE_API_KEY ao .env."
            }

        schema_contexto = """
        Tabelas do Banco de Dados PostgreSQL:
        1. pedidos (id_pedido, cliente_ref, criado_em, status, valor_total, custo_frete, cidade_cliente, estado_cliente, total_itens_preco, desconto_implicito, desconto_perc, mes_pedido, ano_pedido, dia_semana)
        2. itens (id, id_pedido, id_produto, id_material, nome_material, categoria, preco, status)
        3. suprimentos (id_suprimento, id_material, nome_material, quantidade, tempo_entrega, id_fabrica)
        """

        prompt_sistema = f"""
        Você é um especialista em SQL e análise de dados. 
        Seu objetivo é converter uma solicitação de usuário em uma configuração JSON para um dashboard.
        
        Contexto do Banco de Dados:
        {schema_contexto}

        Diretrizes:
        1. Toda a resposta (títulos, eixos) deve ser estritamente em PORTUGUÊS.
        2. IMPORTANTE: O objetivo é gerar imagens estáticas para relatórios (e-mail/Slack), então use títulos claros e evite muitas séries.
        3. Para análises de tempo, **SEMPRE** agrupe por DIA (`DATE(criado_em)`).
        4. **FILTRAGEM DE DATA OBRIGATÓRIA**:
           - **TODA** consulta deve ter: `WHERE pedidos.criado_em BETWEEN :data_inicio AND :data_fim`.
           - Se a consulta for na tabela `itens` ou `suprimentos`, FAÇA JOIN com `pedidos` para poder filtrar pela data do pedido!
           - Exemplo: `SELECT i.nome, count(*) FROM itens i JOIN pedidos p ON i.id_pedido = p.id_pedido WHERE p.criado_em BETWEEN :data_inicio AND :data_fim GROUP BY i.nome`
           - Isso garante que o usuário possa filtrar "Top Produtos" por mês/ano.
        5. **CRÍTICO - LIMITE DE DADOS**:
           - Para gráficos de barra com categorias (ex: produtos, cidades), SEMPRE use `LIMIT 10` ou `LIMIT 15`.
           - Para variáveis numéricas contínuas (ex: desconto_implicito, valor_total), **JAMAIS** agrupe pelo valor exato ou arredondado (ROUND).
           - **OBRIGATÓRIO**: Use `CASE WHEN` para criar faixas (bins).
           - **Descontos**: `desconto_implicito` é R$ (Reais). `desconto_perc` é % (0-100). USE `desconto_perc` para análises de taxa.
             Exemplo BOM:
             `CASE WHEN desconto_perc < 5 THEN '0-5%' WHEN desconto_perc < 10 THEN '5-10%' ELSE '>10%' END`
             Exemplo RUIM: `GROUP BY desconto_implicito` ou usar valores < 1 para porcentagem.
        6. **PREFERÊNCIA POR TABELAS**:
           - Se a consulta listar nomes de produtos, IDs ou materiais específicos (muitas categorias únicas) com uma métrica, PREFIRA usar `"tipo": "tabela"` em vez de gráfico de barras.
           - Gráficos de barra são para COMPARAÇÕES AGREGADAS (ex: Vendas por Categoria, Vendas por Mês).
           - Tabelas são para LISTAGEM DETALHADA (ex: Top 20 Produtos, Produtos com Estoque Baixo).
        7. **ANÁLISES AVANÇADAS (Solicitado pelo usuário)**:
           - Para "Comparar X com Representatividade/Retorno", use `grafico_combinado`.
             - Eixo Y1 (Barra): Volume ou Quantidade.
             - Eixo Y2 (Linha): Porcentagem de Receita, Ticket Médio ou Taxa de Conversão.
           - Exemplo: "Impacto do Desconto":
             - X: Faixa de Desconto
             - Y1: Quantidade de Pedidos (Barra)
             - Y2: Ticket Médio ou % da Receita Total (Linha)

        8. **EXEMPLOS CHAVE (TEMPLATES DE SQL)**:
           - **Analise Complexa (Join Multiplo)**: "Faturamento e Tempo de Entrega por Estado"
             `SELECT p.estado_cliente, SUM(p.valor_total) AS faturamento, ROUND(AVG(s.tempo_entrega), 1) AS tempo_entrega_medio 
              FROM pedidos p 
              JOIN itens i ON p.id_pedido = i.id_pedido 
              JOIN suprimentos s ON i.id_material = s.id_material 
              WHERE p.criado_em BETWEEN :data_inicio AND :data_fim 
              GROUP BY p.estado_cliente 
              ORDER BY faturamento ASC LIMIT 15`

           - **Distribuição (Histograma)**: "Qual faixa de ticket médio fatura mais?"
             `SELECT 
                  CASE 
                      WHEN (p.valor_total / NULLIF(p.total_itens_preco, 0)) < 50 THEN '000-050'
                      WHEN (p.valor_total / NULLIF(p.total_itens_preco, 0)) < 100 THEN '050-100'
                      WHEN (p.valor_total / NULLIF(p.total_itens_preco, 0)) < 200 THEN '100-200'
                      ELSE '200+' 
                  END AS faixa_ticket,
                  SUM(p.valor_total) AS faturamento_total
              FROM pedidos p
              WHERE p.criado_em BETWEEN :data_inicio AND :data_fim
              GROUP BY 1
              ORDER BY 1`
           
           - **Top Ranking Simples**: "Top 10 Cidades que mais compram"
             `SELECT cidade_cliente, COUNT(*) as total_pedidos 
              FROM pedidos 
              WHERE criado_em BETWEEN :data_inicio AND :data_fim 
              GROUP BY cidade_cliente 
              ORDER BY total_pedidos DESC LIMIT 10`

           - **Relacionamento/Trade-off (Gráfico Combinado)**: "Volume de Vendas vs Ticket Médio por Mês"
             `SELECT TO_CHAR(criado_em, 'YYYY-MM') as mes, COUNT(*) as total_vendas, AVG(valor_total) as ticket_medio 
              FROM pedidos 
              WHERE criado_em BETWEEN :data_inicio AND :data_fim 
              GROUP BY 1 
              ORDER BY 1`
             -> **DICA**: Mapeie `total_vendas` no Eixo Y (Barras) e `ticket_medio` no Eixo Y2 (Linha).

        A saída deve ser EXCLUSIVAMENTE um JSON válido com a seguinte estrutura (sem markdown):
        {{
            "nome": "Nome curto para a visão",
            "componentes": [
                {{
                    "tipo": "indicador" | "grafico_barra" | "grafico_linha" | "grafico_combinado" | "tabela",
                    "titulo": "Título do componente",
                    "sql": "Consulta SQL válida para extrair os dados",
                    "eixo_x": "nome_coluna_x" (apenas para gráficos),
                    "eixo_y": "nome_coluna_y" (apenas para gráficos),
                    "eixo_y2": "nome_coluna_y2" (Obrigatório para 'grafico_combinado', eixo direito)
                }}
            ]
        }}
        
        Solicitação do Usuário: {prompt_usuario}
        """

        try:
            resposta = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt_sistema
            )
            texto_resposta = resposta.text
            
            # Limpeza básica caso o modelo retorne markdown
            if "```json" in texto_resposta:
                texto_resposta = texto_resposta.split("```json")[1].split("```")[0]
            elif "```" in texto_resposta:
                texto_resposta = texto_resposta.split("```")[1].split("```")[0]
                
            return json.loads(texto_resposta)
        except Exception as e:
            return {"erro": f"Falha ao gerar visão: {str(e)}"}
