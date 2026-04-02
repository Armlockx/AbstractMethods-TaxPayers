## Dashboard de Opiniao para Live do YouTube

Aplicacao web em Streamlit para:

1. Coletar comentarios de uma live do YouTube (chat ao vivo), com fallback para comentarios do video.
2. Classificar sentimento (`positivo`, `negativo`, `neutro`) e tipo de opiniao (`elogio`, `critica`, `sugestao`, `pergunta`, etc.).
3. Exibir dashboards com graficos, tabela detalhada e arquivos para download (CSV e JSON).

---

## Requisitos

- Python 3.10+
- Chave da **YouTube Data API v3** habilitada no Google Cloud

---

## Instalacao

No diretorio `youtube_opinioes_dashboard`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Executar

```bash
streamlit run app.py
```

Depois abra o endereco local exibido pelo Streamlit (normalmente `http://localhost:8501`).

---

## Como usar

1. Preencha **YouTube API Key**.
2. Informe a **URL da live/video** (ou o ID do video).
3. Escolha a fonte:
   - `auto`: tenta live chat e, se nao encontrar, usa comentarios do video.
   - `somente live chat`
   - `somente comentarios do video`
4. Defina o limite de comentarios e clique em **Coletar e analisar**.

---

## Insights disponiveis

- Volume total de comentarios
- Distribuicao de sentimento
- Distribuicao por tipo de opiniao
- Evolucao temporal dos comentarios (janela de 5 min)
- Termos mais frequentes
- Comentarios mais positivos e mais negativos
- Download:
  - CSV com base analisada
  - JSON com resumo de insights

---

## Observacoes importantes

- O `live chat` so estara disponivel quando a transmissao tiver chat acessivel via API.
- Algumas lives podem restringir comentarios por regiao, idade, status do canal, moderacao ou politica da plataforma.
- A analise de sentimento foi implementada como heuristica lexical em portugues (MVP). Para maior precisao, voce pode trocar por modelos de NLP.

