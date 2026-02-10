# Integração N8N com GoCase Analytics (Gemini + E-mail)

Este guia explica como configurar o N8N para processar relatórios do GoCase Analytics usando IA (Gemini Vision) e enviar os resultados por e-mail, utilizando **Base64** para embutir as imagens diretamente no corpo da mensagem.

## Visão Geral do Fluxo

1.  **Webhook (N8N)**: Recebe os dados e a imagem do Streamlit.
2.  **Preparação (Code Node)**: Formata os dados e prepara o prompt.
3.  **Gemini Node**: Analisa a imagem e gera um texto descritivo.
4.  **Gmail/Outlook Node**: Envia um e-mail com o texto e a imagem embutida (Base64).

---

## 1. Configurando o Webhook

O Streamlit envia um `POST` para o N8N com um JSON contendo metadados e a imagem em Base64.

1.  Crie um nó **Webhook**.
2.  **HTTP Method**: `POST`.
3.  **Path**: `/webhook/analise-visual` (ou o UUID gerado).
4.  **Importante**: O corpo da requisição já contém a imagem em formato Binário ou Base64 (dependendo da sua implementação no Streamlit). O padrão N8N recebe binários automaticamente se o content-type for multipart.

---

## 2. Preparando os Dados (Code Node)

Use um nó **Code** (JavaScript) logo após o Webhook para preparar o prompt e identificar a imagem.

```javascript
// Exemplo de código para preparar o input do Gemini
const item = items[0];
const binaryKey = Object.keys(item.binary)[0]; // Pega a primeira imagem binária

return {
  json: {
    prompt: "Aja como um analista de dados. Descreva os principais insights deste gráfico de vendas. Seja breve.",
  },
  binary: {
    data: item.binary[binaryKey] // Passa a referência da imagem
  }
}
```

---

## 3. Configurando o Gemini (IA Visual)

Para analisar o gráfico recebido:

1.  Adicione o nó **Google Gemini**.
2.  **Resource**: `Model` -> **Operation**: `Generate Content`.
3.  **Model**: `gemini-1.5-flash` (Rápido e eficiente).
4.  **Prompt**: Use a expressão `{{ $json.prompt }}` vindo do nó anterior.
5.  **Input Data**:
    *   **Property Name (Images)**: `data` (ou o nome da sua propriedade binária).

---

## 4. Enviando E-mail com Imagem (Método Base64)

Não precisamos de bucket nem de servidor de arquivos. O e-mail moderno suporta imagens embutidas diretamente no HTML usando Base64.

### Passo 1: Obter a String Base64
A imagem está no formato binário dentro do N8N. Para colocá-la no HTML, precisamos da string Base64.
Você pode usar a expressão `$binary.data.data` (que retorna o base64 da imagem).

### Passo 2: Montar o HTML
No nó de envio de e-mail (Gmail, Outlook, SMTP), use o modo **HTML** e insira a imagem assim:

```html
<h1>Relatório de Performance</h1>
<p><strong>Análise da IA:</strong></p>
<div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px;">
    {{ $json.text }} <!-- Saída do Gemini -->
</div>

<h3>Gráfico Analisado:</h3>
<!-- A mágica acontece aqui: data:image/png;base64,... -->
<!-- $binary.data.data contém a string base64 da imagem no nó atual ou anterior -->
<img src="data:image/png;base64,{{ $binary.data.data }}" alt="Gráfico" width="600" />

<p>Gerado automaticamente por GoCase AI.</p>
```

*Nota: Se o nó do Gmail estiver depois do Gemini, você pode precisar referenciar o binário do nó anterior, ex: `{{ $('Webhook').first().binary.data.data }}`.*

---

## 5. Solução de Problemas

*   **Imagem quebrada no e-mail?**
    *   Verifique se a string Base64 está completa.
    *   Alguns clientes de e-mail antigos bloqueiam Base64 grande. Teste no Gmail e Outlook web.
*   **Erro no Gemini?**
    *   Verifique se a imagem é válida (PNG/JPEG) e não está corrompida.
    *   Tente reduzir a resolução da imagem no Streamlit antes de enviar se estiver muito pesada.
