from __future__ import annotations

import re
from typing import Optional, Tuple

import pandas as pd
from googleapiclient.discovery import build


VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")
URL_PATTERNS = [
    re.compile(r"(?:v=)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:/live/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:/shorts/)([a-zA-Z0-9_-]{11})"),
]


def extract_video_id(video_input: str) -> str:
    candidate = video_input.strip()
    if VIDEO_ID_PATTERN.fullmatch(candidate):
        return candidate

    for pattern in URL_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return match.group(1)

    raise ValueError(
        "Nao foi possivel extrair o ID do video. Informe um URL valido ou o ID de 11 caracteres."
    )


def build_youtube_client(api_key: str):
    if not api_key.strip():
        raise ValueError("Informe uma chave valida da YouTube Data API v3.")
    return build("youtube", "v3", developerKey=api_key.strip(), cache_discovery=False)


def get_video_live_chat_id(client, video_id: str) -> Tuple[Optional[str], str]:
    response = (
        client.videos()
        .list(part="snippet,liveStreamingDetails", id=video_id, maxResults=1)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        raise ValueError("Video nao encontrado ou indisponivel para a API.")

    item = items[0]
    title = item.get("snippet", {}).get("title", "Sem titulo")
    live_chat_id = item.get("liveStreamingDetails", {}).get("activeLiveChatId")
    return live_chat_id, title


def fetch_live_chat_messages(client, live_chat_id: str, max_comments: int = 1500) -> pd.DataFrame:
    rows = []
    page_token = None
    seen_ids = set()

    while len(rows) < max_comments:
        request = client.liveChatMessages().list(
            part="id,snippet,authorDetails",
            liveChatId=live_chat_id,
            maxResults=min(200, max_comments - len(rows)),
            pageToken=page_token,
        )
        response = request.execute()

        items = response.get("items", [])
        if not items:
            break

        for item in items:
            message_id = item.get("id")
            if message_id in seen_ids:
                continue
            seen_ids.add(message_id)

            snippet = item.get("snippet", {})
            author = item.get("authorDetails", {})
            text = snippet.get("displayMessage", "").strip()
            if not text:
                continue

            rows.append(
                {
                    "comment_id": message_id,
                    "author": author.get("displayName", "Anonimo"),
                    "message": text,
                    "published_at": snippet.get("publishedAt"),
                    "author_channel_id": author.get("channelId"),
                    "author_is_moderator": bool(author.get("isChatModerator", False)),
                    "author_is_owner": bool(author.get("isChatOwner", False)),
                    "source": "live_chat",
                }
            )

        next_token = response.get("nextPageToken")
        if not next_token or next_token == page_token:
            break
        page_token = next_token

    return pd.DataFrame(rows)


def fetch_video_comments(client, video_id: str, max_comments: int = 1500) -> pd.DataFrame:
    rows = []
    page_token = None

    while len(rows) < max_comments:
        request = client.commentThreads().list(
            part="id,snippet",
            videoId=video_id,
            maxResults=min(100, max_comments - len(rows)),
            pageToken=page_token,
            textFormat="plainText",
            order="time",
        )
        response = request.execute()
        items = response.get("items", [])
        if not items:
            break

        for item in items:
            top = item.get("snippet", {}).get("topLevelComment", {})
            snippet = top.get("snippet", {})
            text = snippet.get("textDisplay", "").strip()
            if not text:
                continue

            rows.append(
                {
                    "comment_id": top.get("id"),
                    "author": snippet.get("authorDisplayName", "Anonimo"),
                    "message": text,
                    "published_at": snippet.get("publishedAt"),
                    "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
                    "author_is_moderator": False,
                    "author_is_owner": False,
                    "source": "video_comments",
                }
            )

        next_token = response.get("nextPageToken")
        if not next_token or next_token == page_token:
            break
        page_token = next_token

    return pd.DataFrame(rows)
