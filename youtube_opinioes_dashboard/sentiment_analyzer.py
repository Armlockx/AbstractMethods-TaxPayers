from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple

import pandas as pd


POSITIVE_WORDS = {
    "bom",
    "boa",
    "otimo",
    "otima",
    "excelente",
    "incrivel",
    "gostei",
    "amei",
    "parabens",
    "top",
    "show",
    "legal",
    "perfeito",
    "massa",
    "didatico",
    "claro",
}

NEGATIVE_WORDS = {
    "ruim",
    "pessimo",
    "horrivel",
    "fraco",
    "chato",
    "confuso",
    "errado",
    "lento",
    "travando",
    "odio",
    "horrivel",
    "terrivel",
    "decepcionante",
    "mentira",
}

NEGATION_WORDS = {"nao", "nunca", "jamais", "sem"}

SUGGESTION_MARKERS = {"deveria", "poderia", "sugiro", "seria", "melhorar", "melhor"}
SPAM_MARKERS = {"pix", "whatsapp", "telegram", "inscreva", "promo", "cupom"}

STOPWORDS = {
    "a",
    "o",
    "os",
    "as",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "em",
    "para",
    "por",
    "um",
    "uma",
    "com",
    "que",
    "na",
    "no",
    "nas",
    "nos",
    "eu",
    "vc",
    "vcs",
    "voces",
    "vcs",
    "muito",
    "mais",
    "isso",
    "essa",
    "esse",
    "essa",
    "live",
    "video",
}

TOPIC_PATTERNS = {
    "audio": r"\b(audio|som|microfone|microfonia)\b",
    "video": r"\b(video|imagem|resolucao|camera|travando)\b",
    "conteudo": r"\b(conteudo|tema|assunto|explicacao)\b",
    "apresentacao": r"\b(apresentador|narracao|fala|didatica)\b",
    "discordancia": r"\b(discordo|errado|mentira|nada a ver)\b",
    "elogio_geral": r"\b(parabens|otimo|excelente|incrivel)\b",
}


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s\?]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> List[str]:
    return [token for token in _normalize_text(text).split(" ") if token]


def _score_tokens(tokens: List[str]) -> float:
    if not tokens:
        return 0.0

    score = 0.0
    for idx, token in enumerate(tokens):
        prev_token = tokens[idx - 1] if idx > 0 else ""
        is_negated = prev_token in NEGATION_WORDS

        if token in POSITIVE_WORDS:
            score += -1.0 if is_negated else 1.0
        elif token in NEGATIVE_WORDS:
            score += 1.0 if is_negated else -1.0

    return score / max(len(tokens), 1)


def _classify_sentiment(score: float) -> str:
    if score >= 0.05:
        return "positivo"
    if score <= -0.05:
        return "negativo"
    return "neutro"


def _classify_opinion_type(tokens: List[str], original_message: str) -> str:
    token_set = set(tokens)

    if token_set & SPAM_MARKERS:
        return "spam_promocional"
    if "?" in original_message:
        return "pergunta"
    if token_set & SUGGESTION_MARKERS:
        return "sugestao"
    if token_set & NEGATIVE_WORDS:
        return "critica"
    if token_set & POSITIVE_WORDS:
        return "elogio"
    return "opiniao_geral"


def _extract_topics(message: str) -> str:
    normalized = _normalize_text(message)
    topics = [topic for topic, pattern in TOPIC_PATTERNS.items() if re.search(pattern, normalized)]
    if not topics:
        return "outros"
    return ", ".join(topics)


def analyze_comments(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    work_df = df.copy()
    work_df["published_at"] = pd.to_datetime(work_df["published_at"], errors="coerce", utc=True)
    work_df["clean_message"] = work_df["message"].astype(str).map(_normalize_text)
    work_df["tokens"] = work_df["message"].astype(str).map(_tokenize)
    work_df["sentiment_score"] = work_df["tokens"].map(_score_tokens)
    work_df["sentiment_label"] = work_df["sentiment_score"].map(_classify_sentiment)
    work_df["opinion_type"] = work_df.apply(
        lambda row: _classify_opinion_type(row["tokens"], str(row["message"])),
        axis=1,
    )
    work_df["topics"] = work_df["message"].astype(str).map(_extract_topics)
    return work_df


def _count_terms(messages: pd.Series, top_n: int = 15) -> List[Tuple[str, int]]:
    all_tokens: List[str] = []
    for message in messages.dropna().astype(str):
        tokens = _tokenize(message)
        all_tokens.extend([tok for tok in tokens if tok not in STOPWORDS and len(tok) > 2])
    return Counter(all_tokens).most_common(top_n)


def build_insights(df: pd.DataFrame) -> Dict[str, object]:
    if df.empty:
        return {
            "total_comments": 0,
            "sentiment_distribution": {},
            "opinion_distribution": {},
            "top_terms": [],
            "top_positive_comments": [],
            "top_negative_comments": [],
        }

    sentiment_distribution = df["sentiment_label"].value_counts().to_dict()
    opinion_distribution = df["opinion_type"].value_counts().to_dict()
    top_terms = _count_terms(df["message"], top_n=20)

    top_positive = (
        df.sort_values("sentiment_score", ascending=False)
        .head(5)[["author", "message", "sentiment_score"]]
        .to_dict(orient="records")
    )
    top_negative = (
        df.sort_values("sentiment_score", ascending=True)
        .head(5)[["author", "message", "sentiment_score"]]
        .to_dict(orient="records")
    )

    return {
        "total_comments": int(df.shape[0]),
        "sentiment_distribution": sentiment_distribution,
        "opinion_distribution": opinion_distribution,
        "top_terms": top_terms,
        "top_positive_comments": top_positive,
        "top_negative_comments": top_negative,
    }
