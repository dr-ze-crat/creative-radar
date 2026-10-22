"""SQLite 存储层。

每轮抓取写入一个 batch（批次号 = 时间戳），items 保留 30 天；
channel 列区分「综合热榜」(空) 与「分区榜」(分区名)，两者批次互不相干；
升温榜 = 当前批与上一批的排名差；收藏单独一张表。
"""

import datetime
import os
import sqlite3

# channel 列是后加的：老库靠 _migrate 里 ALTER TABLE 补上，所以索引单独建。
SCHEMA = """
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch TEXT NOT NULL,
  source TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT DEFAULT '',
  rank INTEGER NOT NULL,
  hot INTEGER DEFAULT 0,
  hot_text TEXT DEFAULT '',
  fetched_at TEXT NOT NULL,
  channel TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_items_batch ON items(batch);
CREATE INDEX IF NOT EXISTS idx_items_key ON items(source, title);
CREATE INDEX IF NOT EXISTS idx_items_time ON items(fetched_at);

CREATE TABLE IF NOT EXISTS collected(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT DEFAULT '',
  title TEXT NOT NULL,
  url TEXT DEFAULT '',
  hot_text TEXT DEFAULT '',
  added_at TEXT NOT NULL,
  tag TEXT DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_collected_title ON collected(title);

CREATE TABLE IF NOT EXISTS settings(
  key TEXT PRIMARY KEY,
  value TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS materials(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  platform TEXT DEFAULT '',
  kind TEXT DEFAULT 'photo',
  title TEXT NOT NULL,
  author TEXT DEFAULT '',
  author_url TEXT DEFAULT '',
  page_url TEXT DEFAULT '',
  preview_url TEXT DEFAULT '',
  file_url TEXT DEFAULT '',
  license TEXT DEFAULT '',
  license_url TEXT DEFAULT '',
  width INTEGER DEFAULT 0,
  height INTEGER DEFAULT 0,
  duration INTEGER DEFAULT 0,
  added_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_materials_page ON materials(page_url);
"""

KEEP_DAYS = 30


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


class Db:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path
        with self._conn() as c:
            c.executescript(SCHEMA)
            cols = {r["name"] for r in c.execute("PRAGMA table_info(items)")}
            if "channel" not in cols:
                c.execute("ALTER TABLE items ADD COLUMN channel TEXT DEFAULT ''")
            c.execute("CREATE INDEX IF NOT EXISTS idx_items_channel ON items(channel)")
            ccols = {r["name"] for r in c.execute("PRAGMA table_info(collected)")}
            if "tag" not in ccols:  # 选题夹按分区分组导出用
                c.execute("ALTER TABLE collected ADD COLUMN tag TEXT DEFAULT ''")
            mcols = {r["name"] for r in c.execute("PRAGMA table_info(materials)")}
            if "license_url" not in mcols:  # CC 授权必须能点回原文
                c.execute("ALTER TABLE materials ADD COLUMN license_url TEXT DEFAULT ''")

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    # ---------- 写入 ----------

    def save_batch(self, batch: str, items: list[dict], channel: str = "") -> None:
        now = _now()
        rows = [
            (batch, i["source"], i["title"], i.get("url", ""), i["rank"],
             i.get("hot", 0), i.get("hot_text", ""), now, channel)
            for i in items
        ]
        with self._conn() as c:
            c.executemany(
                "INSERT INTO items(batch,source,title,url,rank,hot,hot_text,fetched_at,channel)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                rows,
            )

    def cleanup(self) -> int:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=KEEP_DAYS)).isoformat()
        with self._conn() as c:
            cur = c.execute("DELETE FROM items WHERE fetched_at < ?", (cutoff,))
            return cur.rowcount

    # ---------- 读取 ----------

    def batches(self, n: int = 2, channel: str = "") -> list[str]:
        """取该通道最近的 n 个批次。channel="" 是综合热榜，其余是分区榜。"""
        with self._conn() as c:
            rows = c.execute(
                "SELECT batch FROM items WHERE channel=? GROUP BY batch"
                " ORDER BY batch DESC LIMIT ?",
                (channel, n),
            ).fetchall()
        return [r["batch"] for r in rows]

    def items_of(self, batch: str, channel: str = "") -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT source,title,url,rank,hot,hot_text FROM items"
                " WHERE batch=? AND channel=? ORDER BY source, rank",
                (batch, channel),
            ).fetchall()
        return [dict(r) for r in rows]

    def last_fetch_time(self) -> str:
        """只算综合热榜的时间，别让分区榜抓取顶掉顶部「更新于」。"""
        with self._conn() as c:
            row = c.execute(
                "SELECT MAX(fetched_at) AS t FROM items WHERE channel=''").fetchone()
        return (row["t"] or "") if row else ""

    # ---------- 收藏 ----------

    def collect(self, item: dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO collected(source,title,url,hot_text,added_at,tag)"
                " VALUES(?,?,?,?,?,?)",
                (item.get("source", ""), item["title"], item.get("url", ""),
                 item.get("hot_text", ""), _now(), item.get("tag", "")),
            )

    def uncollect(self, title: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM collected WHERE title=?", (title,))

    def collected(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT source,title,url,hot_text,added_at,tag FROM collected"
                " ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- 界面设置（字号 / 隐藏的分区） ----------

    def settings(self) -> dict:
        with self._conn() as c:
            rows = c.execute("SELECT key,value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def set_setting(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO settings(key,value) VALUES(?,?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    # ---------- 素材账本（只存链接与授权，不存文件） ----------

    def add_material(self, it: dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO materials(platform,kind,title,author,author_url,"
                "page_url,preview_url,file_url,license,license_url,width,height,duration,added_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (it.get("platform", ""), it.get("kind", "photo"), it["title"],
                 it.get("author", ""), it.get("author_url", ""), it.get("page_url", ""),
                 it.get("preview_url", ""), it.get("file_url", ""), it.get("license", ""),
                 it.get("license_url", ""),
                 int(it.get("width") or 0), int(it.get("height") or 0),
                 int(it.get("duration") or 0), _now()),
            )

    def remove_material(self, page_url: str) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM materials WHERE page_url=?", (page_url,))

    def materials(self) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT platform,kind,title,author,author_url,page_url,preview_url,"
                "file_url,license,license_url,width,height,duration,added_at FROM materials"
                " ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]
