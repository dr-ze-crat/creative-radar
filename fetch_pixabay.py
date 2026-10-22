"""Pixabay 素材搜索（图片 + 视频）。

需免费 API key：https://pixabay.com/api/docs/ （注册后在文档页顶部能看到 key）。
额度：100 次 / 60 秒。只读搜索，不下载。
"""

import urllib.parse

from common import http_json

BASE = "https://pixabay.com/api/"
LICENSE = "Pixabay Content License（免费商用，不强制署名）"


class PixabayError(Exception):
    """带可读原因的失败：key 无效 / 超配额 / 网络。"""


def _get(path: str, key: str, params: dict) -> dict:
    if not key or not key.strip():
        raise PixabayError("还没填 Pixabay 的 API key")
    url = BASE + path + "?" + urllib.parse.urlencode({**params, "key": key.strip()})
    try:
        return http_json(url)
    except Exception as e:
        msg = str(e)
        if "400" in msg:
            raise PixabayError("Pixabay key 无效，去 pixabay.com/api/docs 重新复制") from e
        if "429" in msg:
            raise PixabayError("Pixabay 配额用完了（100 次/60 秒），等一分钟") from e
        raise PixabayError(f"连不上 Pixabay：{msg[:80]}") from e


def search_photos(key: str, query: str, per_page: int = 20) -> list[dict]:
    j = _get("", key, {"q": query, "image_type": "photo", "per_page": per_page,
                       "safesearch": "true"})
    out = []
    for h in j.get("hits") or []:
        user = (h.get("user") or "").strip()
        uid = h.get("user_id")
        out.append({
            "platform": "pixabay", "kind": "photo",
            "title": (h.get("tags") or "").strip() or "Pixabay 图片",
            "author": user,
            "author_url": f"https://pixabay.com/users/{user}-{uid}/" if user and uid else "",
            "page_url": h.get("pageURL") or "",
            "preview_url": h.get("webformatURL") or h.get("previewURL") or "",
            "file_url": h.get("largeImageURL") or h.get("webformatURL") or "",
            "license": LICENSE, "license_url": "https://pixabay.com/service/license-summary/",
            "width": int(h.get("imageWidth") or 0),
            "height": int(h.get("imageHeight") or 0),
            "duration": 0,
        })
    return out


def search_videos(key: str, query: str, per_page: int = 15) -> list[dict]:
    j = _get("videos/", key, {"q": query, "per_page": per_page, "safesearch": "true"})
    out = []
    for h in j.get("hits") or []:
        vids = h.get("videos") or {}
        best = vids.get("large") or vids.get("medium") or vids.get("small") or {}
        user = (h.get("user") or "").strip()
        dur = int(h.get("duration") or 0)
        out.append({
            "platform": "pixabay", "kind": "video",
            "title": f"Pixabay 视频 · {dur}s" if dur else "Pixabay 视频",
            "author": user,
            "author_url": f"https://pixabay.com/users/{user}-{h.get('user_id')}/"
                          if user and h.get("user_id") else "",
            "page_url": h.get("pageURL") or "",
            "preview_url": h.get("image") or "",
            "file_url": best.get("url") or "",
            "license": LICENSE, "license_url": "https://pixabay.com/service/license-summary/",
            "width": int(best.get("width") or 0),
            "height": int(best.get("height") or 0),
            "duration": dur,
        })
    return out
