"""Unsplash 图片搜索。

需免费 Access Key：https://unsplash.com/developers （创建 App 即得，demo 50 次/小时）。
只读搜索，不下载。
"""

import urllib.parse

from common import http_json

BASE = "https://api.unsplash.com"
LICENSE = "Unsplash License（免费商用，不强制署名）"
LICENSE_URL = "https://unsplash.com/license"


class UnsplashError(Exception):
    """带可读原因的失败：key 无效 / 超配额 / 网络。"""


def search_photos(key: str, query: str, per_page: int = 20) -> list[dict]:
    if not key or not key.strip():
        raise UnsplashError("还没填 Unsplash 的 Access Key")
    url = (f"{BASE}/search/photos?"
           + urllib.parse.urlencode({"query": query, "per_page": per_page,
                                     "orientation": "landscape"}))
    try:
        j = http_json(url, {"Authorization": f"Client-ID {key.strip()}"})
    except Exception as e:
        msg = str(e)
        if "401" in msg:
            raise UnsplashError("Unsplash key 无效，去 unsplash.com/developers 重新复制") from e
        if "403" in msg or "429" in msg:
            raise UnsplashError("Unsplash 配额用完了（demo 50 次/小时）") from e
        raise UnsplashError(f"连不上 Unsplash：{msg[:80]}") from e

    out = []
    for p in j.get("results") or []:
        urls = p.get("urls") or {}
        user = p.get("user") or {}
        links = p.get("links") or {}
        out.append({
            "platform": "unsplash", "kind": "photo",
            "title": ((p.get("alt_description") or p.get("description") or "").strip()
                      or "Unsplash 图片"),
            "author": user.get("name") or user.get("username") or "",
            "author_url": (user.get("links") or {}).get("html") or "",
            "page_url": links.get("html") or "",
            "preview_url": urls.get("small") or urls.get("regular") or "",
            "file_url": urls.get("full") or urls.get("regular") or "",
            "license": LICENSE, "license_url": LICENSE_URL,
            "width": int(p.get("width") or 0),
            "height": int(p.get("height") or 0),
            "duration": 0,
        })
    return out
