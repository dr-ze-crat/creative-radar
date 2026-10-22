"""各源共用的数据结构与 HTTP 小工具。只用标准库，不引入 requests。"""

import http.client
import json
import urllib.request
from dataclasses import dataclass

# ccMixter 等站点偶尔回超长响应头（一行 > 64KB），标准库会抛 LineTooLong。
http.client._MAXLINE = 1 << 20  # ponytail: 内部常量，放宽到 1MB，够覆盖已知站点

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class Item:
    """一条热榜条目。rank 从 1 开始。hot 为数值热度（无则 0），hot_text 为原始展示文本。"""

    source: str
    title: str
    url: str
    rank: int
    hot: int = 0
    hot_text: str = ""
    sub: str = ""  # 平台子分类（B站 tname 等），没有则为空


def http_get(url: str, headers: dict | None = None, timeout: int = 15) -> str:
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def http_json(url: str, headers: dict | None = None, timeout: int = 15):
    return json.loads(http_get(url, headers, timeout))
