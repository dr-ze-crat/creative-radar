"""百度热搜实时榜。

实测结构（2026-10-22）：data.cards[0].content[0].content 才是条目数组，
条目只有 word / url / index / isTop / hotTag，没有数值热度 —— 故只按排名展示。
"""

from common import Item, http_json

API = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
HEADERS = {"Referer": "https://top.baidu.com/board?tab=realtime"}


def _rows(cards: list) -> list:
    """在 cards 里找出第一个「元素带 content 列表」的容器，取其条目。"""
    for card in cards:
        for block in card.get("content") or []:
            if isinstance(block, dict) and isinstance(block.get("content"), list):
                return block["content"]
    return []


def fetch() -> list[Item]:
    j = http_json(API, HEADERS)
    cards = (j.get("data") or {}).get("cards") or []
    out = []
    for it in _rows(cards):
        word = (it.get("word") or it.get("query") or "").strip()
        if not word:
            continue
        out.append(
            Item(
                source="baidu",
                title=word,
                url=it.get("url") or f"https://www.baidu.com/s?wd={word}",
                rank=len(out) + 1,
                hot=0,
                hot_text="置顶" if it.get("isTop") else "",
            )
        )
    return out


def fetch_tab(tab: str) -> list[Item]:
    """分类榜。实测 tab=finance / sports 可用（30 条）；tab=game 不存在。"""
    j = http_json(
        f"https://top.baidu.com/api/board?platform=wise&tab={tab}",
        {"Referer": f"https://top.baidu.com/board?tab={tab}"},
    )
    cards = (j.get("data") or {}).get("cards") or []
    out = []
    for it in _rows(cards):
        word = (it.get("word") or it.get("query") or "").strip()
        if not word:
            continue
        out.append(
            Item(
                source="baidu",
                title=word,
                url=it.get("url") or f"https://www.baidu.com/s?wd={word}",
                rank=len(out) + 1,
                hot=0,
                hot_text="置顶" if it.get("isTop") else "",
            )
        )
    return out
