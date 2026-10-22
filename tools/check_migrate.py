"""验证旧库迁移：复制生产库到临时目录，加 channel/tag 列后旧数据不丢、能按通道查批次。

    python tools/check_migrate.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from db import Db  # noqa: E402


def cols(path, table):
    c = sqlite3.connect(path)
    try:
        return [r[1] for r in c.execute(f"PRAGMA table_info({table})")]
    finally:
        c.close()


def count(path, table):
    c = sqlite3.connect(path)
    try:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        c.close()


def main():
    src = os.path.join(os.environ.get("LOCALAPPDATA") or BASE, "创作雷达", "radar.db")
    assert os.path.exists(src), f"没有生产库：{src}"
    tmp = os.path.join(tempfile.mkdtemp(), "radar.db")
    shutil.copy(src, tmp)
    before_items, before_picks = cols(tmp, "items"), cols(tmp, "collected")
    n_items = count(tmp, "items")
    n_picks = count(tmp, "collected")

    db = Db(tmp)  # 构造即迁移

    assert "channel" in cols(tmp, "items"), cols(tmp, "items")
    assert "tag" in cols(tmp, "collected"), cols(tmp, "collected")
    assert count(tmp, "items") == n_items, f"迁移丢条目：{n_items}"
    assert count(tmp, "collected") == n_picks, f"迁移丢收藏：{n_picks}"
    old = sqlite3.connect(tmp).execute(
        "SELECT COUNT(*) FROM items WHERE channel=''").fetchone()[0]
    groups = sqlite3.connect(tmp).execute(
        "SELECT channel, COUNT(*) FROM items GROUP BY channel").fetchall()
    assert sum(n for _, n in groups) == n_items, f"迁移丢条目：{n_items} -> {groups}"
    assert dict(groups)[""] == old
    assert len(db.batches(3)) >= 1, "综合批次为空"
    print(f"迁移通过：items {before_items} -> {cols(tmp, 'items')}，"
          f"collected {before_picks} -> {cols(tmp, 'collected')}")
    print(f"{n_items} 条热榜按通道分组：{groups}，{n_picks} 条收藏保留（旧收藏 tag 为空→未分类）")
    print("最近综合批次：", db.batches(3))


if __name__ == "__main__":
    main()
