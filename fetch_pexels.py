"""Pexels 素材搜索（图片 + 视频）。

需要免费 API key：https://www.pexels.com/api/ ，在「素材」页填一次即可。
只读搜索，不下载任何文件；收藏只记链接与授权信息。
"""

import urllib.parse

from common import http_json

BASE = "https://api.pexels.com"
LICENSE = "Pexels License（免费商用，不强制署名）"


class PexelsError(Exception):
    """带可读原因的失败：key 无效 / 超配额 / 网络。"""


def _get(path: str, key: str, params: dict) -> dict:
    if not key or not key.strip():
        raise PexelsError("还没填 Pexels 的 API key")
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    try:
        return http_json(url, {"Authorization": key.strip()})
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg:
            raise PexelsError("key 无效或已被吊销，去 pexels.com/api 重新复制") from e
        if "429" in msg:
            raise PexelsError("这个 key 今天的配额用完了（200 次/小时），等一会儿再搜") from e
        raise PexelsError(f"连不上 Pexels：{msg[:80]}") from e


def search_photos(key: str, query: str, page: int = 1, per_page: int = 24) -> list[dict]:
    j = _get("/v1/search", key, {"query": query, "page": page,
                                 "per_page": per_page, "orientation": "landscape"})
    out = []
    for p in j.get("photos") or []:
        src = p.get("src") or {}
        out.append({
            "platform": "pexels", "kind": "photo",
            "title": (p.get("alt") or "").strip() or "Pexels 图片",
            "author": p.get("photographer") or "",
            "author_url": p.get("photographer_url") or "",
            "page_url": p.get("url") or "",
            "preview_url": src.get("medium") or src.get("large") or "",
            "file_url": src.get("original") or "",
            "license": LICENSE,
            "width": int(p.get("width") or 0),
            "height": int(p.get("height") or 0),
            "duration": 0,
        })
    return out


def search_videos(key: str, query: str, page: int = 1, per_page: int = 15) -> list[dict]:
    j = _get("/videos/search", key, {"query": query, "page": page,
                                     "per_page": per_page, "orientation": "landscape"})
    out = []
    for v in j.get("videos") or []:
        user = v.get("user") or {}
        files = [f for f in (v.get("video_files") or []) if f.get("link")]
        best = max(files, key=lambda f: (f.get("width") or 0), default={})
        dur = int(v.get("duration") or 0)
        out.append({
            "platform": "pexels", "kind": "video",
            "title": f"Pexels 视频 · {dur}s" if dur else "Pexels 视频",
            "author": user.get("name") or "",
            "author_url": user.get("url") or "",
            "page_url": v.get("url") or "",
            "preview_url": v.get("image") or "",
            "file_url": best.get("link") or "",
            "license": LICENSE,
            "width": int(v.get("width") or 0),
            "height": int(v.get("height") or 0),
            "duration": dur,
        })
    return out
