import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from io import BytesIO
import textwrap

import re

def format_number(x, pos):
    """Formata números para K (milhares) e M (milhões) para evitar notação científica."""
    if x >= 1000000:
        return f'{x/1000000:.1f}M'
    elif x >= 1000:
        return f'{x/1000:.0f}K'
    else:
        return f'{x:.0f}'

def sort_dataframe_logically(df, col):
    """
    Tenta ordenar o DataFrame de forma lógica para o eixo X.
    Resolve problemas de faixas como '5-10%' vindo depois de '10-15%' (ordem alfabética errada).
    """
    try:
        if df.empty or col not in df.columns:
            return df

        # Se já for numérico ou data, ordena direto
        if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
            return df.sort_values(by=col)

        # Lógica para Strings (Faixas, Meses, etc)
        df = df.copy()
        
        def extract_sort_key(val):
            s = str(val).strip()
            
            # Padrão para faixas numéricas: "0-5%", ">15%", "<10", "R$ 100-200"
            # Extrai o primeiro número encontrado
            match = re.search(r'(\d+[.,]?\d*)', s)
            if match:
                num = float(match.group(1).replace(',', '.'))
                # Ajuste para modificadores
                if '>' in s: num += 0.1 # Garante que >15 venha depois de 15
                if '<' in s: num -= 0.1
                return num
            
            return s # Fallback para string normal

        df['_sort_key'] = df[col].apply(extract_sort_key)
        df_sorted = df.sort_values(by='_sort_key').drop(columns=['_sort_key'])
        return df_sorted

    except Exception:
        # Se der erro na lógica customizada, retorna original (ou poderia tentar sort simples)
        return df

import pandas as pd

def wrap_labels(ax, width=15):
    """Quebra linhas de labels longos."""
    labels = []
    # Garantir que temos labels para iterar
    if not ax.get_xticklabels():
        return
        
    for label in ax.get_xticklabels():
        text = label.get_text()
        labels.append(textwrap.fill(text, width=width))
    ax.set_xticklabels(labels, rotation=45, ha='right')

def gerar_grafico(df, tipo, titulo, eixo_x, eixo_y, eixo_y2=None):
    """
    Gera um gráfico estático (Matplotlib/Seaborn) a partir de um DataFrame.
    Retorna: BytesIO buffer contendo a imagem PNG.
    """
    try:
        # Configuração de Estilo
        plt.figure(figsize=(12, 7)) 
        sns.set_theme(style="white", font_scale=1.1)
        
        # Validação básica
        if eixo_x not in df.columns or eixo_y not in df.columns:
            return None, f"Colunas não encontradas: {eixo_x}, {eixo_y}"

        # --- ORDENAÇÃO INTELIGENTE ---
        # Antes de plotar, garantimos que o eixo X siga uma ordem lógica
        # (Ex: numérico, cronológico ou faixas de valores)
        df = sort_dataframe_logically(df, eixo_x)

        ax = None
        
        if tipo == 'grafico_barra':
            # Barplot
            ax = sns.barplot(
                data=df, x=eixo_x, y=eixo_y, 
                palette="viridis", hue=eixo_x, legend=False,
                edgecolor="black", linewidth=0.5 # Borda suave para contraste
            )
            ax.set_title(titulo, fontsize=16, weight='bold', pad=20)
            ax.set_xlabel(eixo_x, fontsize=12, weight='bold')
            ax.set_ylabel(eixo_y, fontsize=12, weight='bold')
            
            # Melhorar Grid
            ax.yaxis.grid(True, linestyle='--', which='major', color='grey', alpha=0.25)
            ax.xaxis.grid(False)
            
            wrap_labels(ax)

        elif tipo == 'grafico_linha':
            ax = sns.lineplot(data=df, x=eixo_x, y=eixo_y, marker='o', linewidth=3, markersize=8)
            ax.set_title(titulo, fontsize=16, weight='bold', pad=20)
            ax.set_xlabel(eixo_x, fontsize=12, weight='bold')
            ax.set_ylabel(eixo_y, fontsize=12, weight='bold')
            
            ax.grid(True, linestyle='--', alpha=0.5)
            wrap_labels(ax)

        elif tipo == 'grafico_combinado':
            if not eixo_y2 or eixo_y2 not in df.columns:
                return None, "Eixo Y2 necessário para gráfico combinado"
            
            # Converter eixo X para string para garantir alinhamento entre Bar e Line
            # Isso evita o erro de "tz must be string" e desalinhamento de eixos
            df_comb = df.copy()
            df_comb[eixo_x] = df_comb[eixo_x].astype(str)

            fig, ax1 = plt.subplots(figsize=(12, 7))
            sns.set_theme(style="white")
            
            # Gráfico de Barras (Eixo 1) -> Usa eixo categórico (Strings)
            sns.barplot(
                data=df_comb, x=eixo_x, y=eixo_y, 
                hue=eixo_x, ax=ax1, palette="viridis", 
                alpha=0.6, legend=False, edgecolor="None"
            )
            ax1.set_ylabel(eixo_y, color='#2c3e50', fontsize=12, weight='bold')
            ax1.tick_params(axis='y', labelcolor='#2c3e50')
            ax1.yaxis.set_major_formatter(ticker.FuncFormatter(format_number))
            ax1.grid(False) 

            # Gráfico de Linha (Eixo 2) -> Agora também usa strings, alinhando com as barras
            ax2 = ax1.twinx()
            sns.lineplot(data=df_comb, x=eixo_x, y=eixo_y2, ax=ax2, color='#e74c3c', marker='o', linewidth=3)
            ax2.set_ylabel(eixo_y2, color='#c0392b', fontsize=12, weight='bold')
            ax2.tick_params(axis='y', labelcolor='#c0392b')
            ax2.yaxis.set_major_formatter(ticker.FuncFormatter(format_number))
            ax2.grid(False)
            
            plt.title(titulo, fontsize=16, weight='bold', pad=20)
            
            # Ajuste de Labels no Eixo X (compartilhado)
            wrap_labels(ax1)
            ax = ax1 # Referência para layout

        else:
            plt.close()
            return None, f"Tipo de gráfico desconhecido: {tipo}"

        # Aplicar formatação de números no eixo Y do ax principal
        if ax and tipo != 'grafico_combinado':
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_number))
            
        # Remover bordas desnecessárias (spines)
        if ax:
            sns.despine(ax=ax, left=True, bottom=False)

        plt.tight_layout()
        
        # Salvar em buffer com bbox_inches='tight' para não cortar textos
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()
        
        return buf, None

    except Exception as e:
        plt.close()
        return None, str(e)

def gerar_tabela_imagem(df, titulo="Tabela"):
    """
    Converte um DataFrame em uma imagem PNG usando Matplotlib com alta qualidade.
    """
    try:
        # 1. Preparar Dados (Formatação e Wrap)
        df_display = df.copy()
        
        WIDTH_WRAP = 35
        def smart_wrap(text, width=WIDTH_WRAP):
            return textwrap.fill(str(text), width=width)

        for col in df_display.columns:
            if pd.api.types.is_float_dtype(df_display[col]):
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            elif pd.api.types.is_string_dtype(df_display[col]) or pd.api.types.is_object_dtype(df_display[col]):
                 df_display[col] = df_display[col].apply(lambda x: smart_wrap(x, width=WIDTH_WRAP))
        
        # 2. Configuração de Tamanho Inteligente
        num_cols = len(df.columns)
        num_rows = len(df)
        
        # Calcular linhas reais (altura do conteudo)
        total_text_lines = 0
        row_heights = [] # Para armazenar altura necessária de cada linha
        
        # Header counts as 2 lines approx
        total_text_lines += 2
        
        for idx, row in df_display.iterrows():
            max_lines_in_row = 1
            for item in row:
                if isinstance(item, str):
                    max_lines_in_row = max(max_lines_in_row, item.count('\n') + 1)
            row_heights.append(max_lines_in_row)
            total_text_lines += max_lines_in_row

        # Fatores de escala
        base_height_per_line = 0.4 
        altura_total = max(2, total_text_lines * base_height_per_line + 1) # +1 para título
        
        largura_total = max(8, min(num_cols * 4, 22))
        
        plt.figure(figsize=(largura_total, altura_total))
        
        # 3. Desenhar Tabela
        ax = plt.gca()
        ax.axis('off')
        
        tabela = plt.table(
            cellText=df_display.values,
            colLabels=df_display.columns,
            loc='upper center', 
            cellLoc='left',
            colLoc='center',
            edges='horizontal' 
        )

        # 4. Ajuste Fino de Altura por Linha
        # Iterar cells para ajustar altura conforme o conteudo
        cell_dict = tabela.get_celld()
        
        for row in range(num_rows + 1):
             # row 0 is header
             if row == 0:
                 height = 0.1
             else:
                 # row indices in data are 0-based, so row in table is data_index + 1
                 # row_heights array index is row - 1
                 lines = row_heights[row-1]
                 height = lines * 0.08 + 0.05 # Altura base + extra por linha

             for col in range(num_cols):
                 if (row, col) in cell_dict:
                     cell = cell_dict[(row, col)]
                     cell.set_height(height)
                     
                     cell.set_linewidth(0)
                     if row >= 0:
                         cell.set_edgecolor('#eeeeee')
                         cell.set_linewidth(1)
                     
                     # Estilo
                     if row == 0:
                        cell.set_text_props(weight='bold', color='white', size=11)
                        cell.set_facecolor('#2c3e50')
                        cell.set_text_props(ha='center')
                     else:
                        cell.set_facecolor('white' if row % 2 != 0 else '#fdfdfd')

        plt.title(titulo, fontsize=14, weight='bold', color='#333333', pad=10)
        
        # 5. Salvar (DPI Reduzido para ficar "menor" na tela)
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        plt.close()
        
        return buf, None

    except Exception as e:
        plt.close()
        return None, str(e)
