"""微博热搜榜（免登录 ajax 接口）。"""

from urllib.parse import quote

from common import Item, http_json

API = "https://weibo.com/ajax/side/hotSearch"
HEADERS = {"Referer": "https://weibo.com/"}


def fetch() -> list[Item]:
    j = http_json(API, HEADERS)
    rows = (j.get("data") or {}).get("realtime") or []
    out = []
    for it in rows:
        if it.get("is_ad"):
            continue
        word = (it.get("word") or it.get("note") or "").strip()
        if not word:
            continue
        num = it.get("num") or it.get("raw_hot") or 0
        out.append(
            Item(
                source="weibo",
                title=word,
                url=f"https://s.weibo.com/weibo?q=%23{quote(word)}%23",
                rank=len(out) + 1,
                hot=int(num) if str(num).isdigit() else 0,
                hot_text=f"{int(num) / 10000:.1f}万" if str(num).isdigit() else "",
            )
        )
    return out


def fetch_band(band: str = "ent") -> list[Item]:
    """分类榜。band=ent 为文娱榜，实测 51 条。"""
    from urllib.parse import quote as _q

    j = http_json("https://weibo.com/ajax/statuses/hot_band?band=" + band, HEADERS)
    rows = (j.get("data") or {}).get("band_list") or []
    out = []
    for it in rows:
        word = (it.get("word_scheme") or it.get("note") or "").strip()
        if not word:
            continue
        num = it.get("num") or 0
        out.append(
            Item(
                source="weibo",
                title=word,
                url=f"https://s.weibo.com/weibo?q=%23{_q(word)}%23",
                rank=len(out) + 1,
                hot=int(num) if str(num).isdigit() else 0,
                hot_text=f"{int(num) / 10000:.1f}万" if str(num).isdigit() else "",
            )
        )
    return out
