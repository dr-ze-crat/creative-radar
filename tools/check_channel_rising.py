"""端到端验证 P1：分区榜落库后，下一次抓取能算出分区内升温（需要联网）。

    python tools/check_channel_rising.py

不碰生产库：用临时库 + 真实 B站 分区榜。
"""

import os
import sqlite3
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from app import Api  # noqa: E402
from db import Db  # noqa: E402


def main() -> None:
    api = Api.__new__(Api)  # 只要 db 和缓存，不跑 __init__（避开 pywebview 窗口）
    api.db = Db(os.path.join(tempfile.mkdtemp(), "t.db"))
    api._ch_cache = {}

    first = api.channel("游戏")
    assert first["ok"] and first["count"] > 0, first
    batch = api.db.batches(1, "游戏")[0]
    assert len(api.db.items_of(batch, "游戏")) == first["count"]

    # 把上一批每条都压低 5 名，模拟「10 分钟前排名更低」
    with sqlite3.connect(api.db.path) as c:
        c.execute("UPDATE items SET rank=rank+5 WHERE batch=? AND channel='游戏'", (batch,))

    api._ch_cache.clear()
    second = api.channel("游戏")
    risen = second["rising"]
    assert len(risen) >= 20, f"升温条目太少：{len(risen)}"
    assert all(r["delta"] > 0 for r in risen), "升温列表混入未升温条目"
    assert risen[0]["delta"] == 5, risen[0]
    print(f"分区升温通过：{second['count']} 条入库，{len(risen)} 条升温，"
          f"最大 +{risen[0]['delta']}（{risen[0]['title']}）")


if __name__ == "__main__":
    main()
