"""音乐素材搜索：ccMixter（免 key）+ Jamendo（需 client_id）。

⚠ 这两个源的授权都是 Creative Commons 变体，**很多是 NC（禁止商用）**。
账本会逐条记下 license_name 与 license_url，用之前自己看一眼。
"""

import urllib.parse

from common import http_json

CCMIXTER = "https://ccmixter.org/api/query"
JAMENDO = "https://api.jamendo.com/v3.0/tracks/"


class MusicError(Exception):
    """带可读原因的失败。"""


def search_ccmixter(query: str, limit: int = 12) -> list[dict]:
    url = (f"{CCMIXTER}?f=json&limit={limit}&search="
           + urllib.parse.quote(query))
    try:
        j = http_json(url)
    except Exception as e:
        raise MusicError(f"连不上 ccMixter：{str(e)[:80]}") from e
    if not isinstance(j, list):
        return []

    out = []
    for u in j:
        files = u.get("files") or []
        mp3 = next((f for f in files
                    if f.get("download_url")
                    and (f.get("file_nicname") == "mp3"
                         or str(f.get("file_name", "")).endswith(".mp3"))), None)
        if not mp3:
            continue
        tags = (u.get("upload_tags") or "").strip(",").split(",")
        title = (u.get("upload_name") or "").strip() or "ccMixter 音乐"
        out.append({
            "platform": "ccmixter", "kind": "audio",
            "title": title,
            "author": u.get("user_name") or "",
            "author_url": u.get("artist_page_url") or "",
            "page_url": u.get("file_page_url") or "",
            "preview_url": "",
            "file_url": mp3.get("download_url") or "",
            "license": (u.get("license_name") or "Creative Commons"),
            "license_url": u.get("license_url") or "",
            "width": 0, "height": 0, "duration": 0,
            "tags": [t for t in tags if t and not t.startswith("bpm_")][:6],
        })
    return out


def search_jamendo(client_id: str, query: str, limit: int = 15) -> list[dict]:
    if not client_id or not client_id.strip():
        raise MusicError("还没填 Jamendo 的 client_id")
    url = (f"{JAMENDO}?client_id={urllib.parse.quote(client_id.strip())}"
           f"&format=json&limit={limit}&audioformat=mp32&search="
           + urllib.parse.quote(query))
    try:
        j = http_json(url)
    except Exception as e:
        raise MusicError(f"连不上 Jamendo：{str(e)[:80]}") from e
    head = j.get("headers") or {}
    if head.get("status") != "success":
        raise MusicError(f"Jamendo 返回错误：{(head.get('error_message') or '')[:80]}")

    out = []
    for t in j.get("results") or []:
        out.append({
            "platform": "jamendo", "kind": "audio",
            "title": t.get("name") or "Jamendo 音乐",
            "author": t.get("artist_name") or "",
            "author_url": t.get("artist_shareurl") or "",
            "page_url": t.get("shareurl") or "",
            "preview_url": t.get("image") or "",
            "file_url": t.get("audiodownload") or t.get("audio") or "",
            "license": (t.get("license_ccurl") or "Creative Commons").rstrip("/").rsplit("/", 1)[-1],
            "license_url": t.get("license_ccurl") or "",
            "width": 0, "height": 0,
            "duration": int(t.get("duration") or 0),
        })
    return out
