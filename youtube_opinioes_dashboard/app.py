from __future__ import annotations

import json
from typing import Dict, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from googleapiclient.errors import HttpError

from sentiment_analyzer import analyze_comments, build_insights
from youtube_client import (
    build_youtube_client,
    extract_video_id,
    fetch_live_chat_messages,
    fetch_video_comments,
    get_video_live_chat_id,
)


st.set_page_config(page_title="Analise de Comentarios YouTube", layout="wide")
st.title("Dashboard de Opiniao - Live do YouTube")
st.caption(
    "Coleta comentarios de live/chat ou comentarios do video e gera analises de sentimento e opiniao."
)


def _sentiment_metrics(insights: Dict[str, object]) -> Tuple[int, int, int]:
    distribution = insights.get("sentiment_distribution", {})
    pos = int(distribution.get("positivo", 0))
    neg = int(distribution.get("negativo", 0))
    neu = int(distribution.get("neutro", 0))
    return pos, neg, neu


with st.sidebar:
    st.header("Configuracoes")
    api_key = st.text_input("YouTube API Key", type="password")
    video_input = st.text_input("URL ou ID da live/video")
    mode = st.selectbox(
        "Fonte de comentarios",
        (
            "auto (live chat e fallback para comentarios)",
            "somente live chat",
            "somente comentarios do video",
        ),
    )
    max_comments = st.slider("Maximo de comentarios", min_value=100, max_value=5000, value=1500, step=100)
    run_button = st.button("Coletar e analisar", use_container_width=True)


if run_button:
    if not api_key.strip() or not video_input.strip():
        st.error("Informe a chave da API e o URL/ID do video.")
        st.stop()

    try:
        video_id = extract_video_id(video_input)
        client = build_youtube_client(api_key)

        live_chat_id, title = get_video_live_chat_id(client, video_id)
        data_source = ""
        comments_df = pd.DataFrame()

        if mode == "somente live chat":
            if not live_chat_id:
                raise ValueError("Esta transmissao nao possui live chat ativo/disponivel na API.")
            comments_df = fetch_live_chat_messages(client, live_chat_id, max_comments=max_comments)
            data_source = "live_chat"
        elif mode == "somente comentarios do video":
            comments_df = fetch_video_comments(client, video_id, max_comments=max_comments)
            data_source = "video_comments"
        else:
            if live_chat_id:
                comments_df = fetch_live_chat_messages(client, live_chat_id, max_comments=max_comments)
                data_source = "live_chat"
            if comments_df.empty:
                comments_df = fetch_video_comments(client, video_id, max_comments=max_comments)
                data_source = "video_comments"

        if comments_df.empty:
            st.warning(
                "Nenhum comentario encontrado. Verifique se a live/video possui mensagens publicas para esta conta/API."
            )
            st.stop()

        analyzed_df = analyze_comments(comments_df)
        insights = build_insights(analyzed_df)

        st.success(f"Coleta concluida para: {title}")
        st.info(f"Fonte utilizada: {data_source}")

        pos, neg, neu = _sentiment_metrics(insights)
        total_comments = int(insights.get("total_comments", 0))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total comentarios", f"{total_comments}")
        col2.metric("Positivos", f"{pos}")
        col3.metric("Negativos", f"{neg}")
        col4.metric("Neutros", f"{neu}")

        chart_col1, chart_col2 = st.columns(2)

        sentiment_df = (
            pd.Series(insights["sentiment_distribution"], name="qtd")
            .rename_axis("sentimento")
            .reset_index()
            .sort_values("qtd", ascending=False)
        )
        fig_sentiment = px.bar(
            sentiment_df,
            x="sentimento",
            y="qtd",
            title="Distribuicao de sentimento",
            color="sentimento",
        )
        chart_col1.plotly_chart(fig_sentiment, use_container_width=True)

        opinion_df = (
            pd.Series(insights["opinion_distribution"], name="qtd")
            .rename_axis("tipo")
            .reset_index()
            .sort_values("qtd", ascending=False)
        )
        fig_opinion = px.pie(opinion_df, values="qtd", names="tipo", title="Tipos de opiniao")
        chart_col2.plotly_chart(fig_opinion, use_container_width=True)

        analyzed_df["published_local"] = pd.to_datetime(analyzed_df["published_at"], errors="coerce", utc=True)
        timeline_df = (
            analyzed_df.dropna(subset=["published_local"])
            .set_index("published_local")
            .resample("5min")
            .size()
            .reset_index(name="qtd")
        )
        if not timeline_df.empty:
            fig_timeline = px.line(
                timeline_df,
                x="published_local",
                y="qtd",
                title="Volume de comentarios ao longo do tempo (janela de 5 min)",
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

        top_terms = insights.get("top_terms", [])
        terms_df = pd.DataFrame(top_terms, columns=["termo", "qtd"])
        if not terms_df.empty:
            fig_terms = px.bar(terms_df, x="termo", y="qtd", title="Termos mais frequentes")
            st.plotly_chart(fig_terms, use_container_width=True)

        tabs = st.tabs(["Principais comentarios", "Dados completos", "Download"])

        with tabs[0]:
            st.subheader("Mais positivos")
            pos_df = pd.DataFrame(insights.get("top_positive_comments", []))
            st.dataframe(pos_df, use_container_width=True)

            st.subheader("Mais negativos")
            neg_df = pd.DataFrame(insights.get("top_negative_comments", []))
            st.dataframe(neg_df, use_container_width=True)

        with tabs[1]:
            view_df = analyzed_df[
                [
                    "author",
                    "message",
                    "sentiment_label",
                    "sentiment_score",
                    "opinion_type",
                    "topics",
                    "published_at",
                    "source",
                ]
            ].copy()
            st.dataframe(view_df, use_container_width=True)

        with tabs[2]:
            csv_bytes = analyzed_df.to_csv(index=False).encode("utf-8")
            json_bytes = json.dumps(insights, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label="Baixar CSV com comentarios analisados",
                data=csv_bytes,
                file_name=f"{video_id}_comentarios_analisados.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Baixar JSON de insights",
                data=json_bytes,
                file_name=f"{video_id}_insights.json",
                mime="application/json",
            )

    except HttpError as exc:
        st.error(f"Erro na API do YouTube: {exc}")
    except Exception as exc:  # noqa: BLE001 - errors are shown to end users in Streamlit.
        st.error(f"Falha ao processar: {exc}")
