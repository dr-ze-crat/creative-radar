"""B站热门视频榜。"""

from common import Item, http_json

API = "https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1"
HEADERS = {"Referer": "https://www.bilibili.com/"}


def fetch() -> list[Item]:
    j = http_json(API, HEADERS)
    rows = (j.get("data") or {}).get("list") or []
    out = []
    for i, it in enumerate(rows, 1):
        title = (it.get("title") or "").strip()
        if not title:
            continue
        bvid = it.get("bvid") or ""
        view = int(((it.get("stat") or {}).get("view")) or 0)
        out.append(
            Item(
                source="bilibili",
                title=title,
                url=f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                rank=i,
                hot=view,
                hot_text=f"{view / 10000:.1f}万播放" if view else "",
                sub=(it.get("tname") or "").strip(),
            )
        )
    return out


RANK_API = "https://api.bilibili.com/x/web-interface/ranking/v2?rid={rid}&type=all"


def fetch_rank(rid: int) -> list[Item]:
    """按分区 rid 取排行（实测 2026-10-22：除 71 综艺外基本都有 60-97 条）。"""
    j = http_json(RANK_API.format(rid=rid), HEADERS)
    rows = (j.get("data") or {}).get("list") or []
    out = []
    for i, it in enumerate(rows, 1):
        title = (it.get("title") or "").strip()
        if not title:
            continue
        bvid = it.get("bvid") or ""
        view = int(((it.get("stat") or {}).get("view")) or 0)
        out.append(
            Item(
                source="bilibili",
                title=title,
                url=f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                rank=i,
                hot=view,
                hot_text=f"{view / 10000:.1f}万播放" if view else "",
                sub=(it.get("tname") or "").strip(),
            )
        )
    return out


TAG_API = "https://api.bilibili.com/x/tag/archive/tags?bvid={bvid}"


def fetch_tags(bvid: str) -> list[str]:
    """取单个视频的标签（免登录）。用于按作品/游戏名做二级分类。"""
    if not bvid:
        return []
    try:
        j = http_json(TAG_API.format(bvid=bvid), HEADERS)
        rows = j.get("data") or []
        return [str(r.get("tag_name") or "").strip() for r in rows
                if str(r.get("tag_name") or "").strip()]
    except Exception:
        return []
