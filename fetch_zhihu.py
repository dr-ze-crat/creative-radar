"""知乎热榜。

实测（2026-10-22）：www.zhihu.com/api/v3/... 需登录 cookie（401），
改用 api.zhihu.com/topstory/hot-list，免登录可用；detail_text 形如「564 万热度」。
"""

from common import Item, http_json

API = "https://api.zhihu.com/topstory/hot-list?limit=50"
HEADERS = {"Referer": "https://www.zhihu.com/hot"}


def fetch() -> list[Item]:
    j = http_json(API, HEADERS)
    rows = j.get("data") or []
    out = []
    for d in rows:
        t = d.get("target") or {}
        title = (t.get("title") or "").strip()
        if not title:
            continue
        qid = t.get("id")
        out.append(
            Item(
                source="zhihu",
                title=title,
                url=f"https://www.zhihu.com/question/{qid}" if qid else "",
                rank=len(out) + 1,
                hot_text=(d.get("detail_text") or "").strip(),
            )
        )
    return out
