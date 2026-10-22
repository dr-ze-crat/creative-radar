"""离线自检（不联网）：聚类 / 标签 / 入库 / 升温 / 剪贴板。

    python selfcheck.py

任何一条断言失败即说明核心逻辑坏了。
"""

import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import Api, build_clusters, tag_of  # noqa: E402
from clip import copy_text, read_text  # noqa: E402
from db import Db  # noqa: E402


def main() -> None:
    # 1. 同题归并：只有跨源且相似才合并
    items = [
        {"source": "baidu", "title": "银行回应每天仅营业3.5小时"},
        {"source": "weibo", "title": "银行回应每天仅营业3.5小时"},
        {"source": "weibo", "title": "一个完全无关的话题内容"},
    ]
    groups = build_clusters(items)
    assert len(groups) == 1, f"应只有 1 组，实际 {len(groups)}"
    assert sorted(groups[0]) == [0, 1], f"应归并 0 与 1，实际 {groups[0]}"

    # 2. 领域标签
    assert tag_of("原神新版本上线了") == "游戏"
    assert tag_of("某明星官宣结婚") == "娱乐"
    assert tag_of("随便一句没有关键词的话") == "综合"

    # 3. 入库 + 升温差（rank 变小 = 升温）
    db = Db(os.path.join(tempfile.mkdtemp(), "t.db"))
    db.save_batch("20260101000000", [
        {"source": "weibo", "title": "A", "rank": 10},
        {"source": "weibo", "title": "B", "rank": 20},
    ])
    db.save_batch("20260101001000", [
        {"source": "weibo", "title": "A", "rank": 3},
        {"source": "weibo", "title": "B", "rank": 25},
    ])
    prev = {(i["source"], i["title"]): i["rank"] for i in db.items_of(db.batches(2)[1])}
    delta = {(i["source"], i["title"]): prev[(i["source"], i["title"])] - i["rank"]
             for i in db.items_of(db.batches(1)[0])}
    assert delta[("weibo", "A")] == 7, delta
    assert delta[("weibo", "B")] == -5, delta

    # 4. 收藏去重 + 按分区分组导出
    api = Api.__new__(Api)  # 只测纯逻辑，不碰真实数据目录
    api.db = db
    db.collect({"source": "weibo", "title": "A", "url": "u", "tag": "娱乐"})
    db.collect({"source": "weibo", "title": "A", "url": "u", "tag": "娱乐"})
    db.collect({"source": "bilibili", "title": "B", "tag": "游戏"})
    db.collect({"source": "", "title": "C"})  # 缺字段的旧收藏 → 未分类
    assert [r["title"] for r in db.collected()] == ["C", "B", "A"], db.collected()
    assert db.collected()[-1]["tag"] == "娱乐", db.collected()
    md = api.export_md()
    assert md.index("## 游戏") < md.index("## 娱乐") < md.index("## 未分类"), md
    assert "- **[B站]** B" in md and "来源未知" in md, md
    db.uncollect("A"); db.uncollect("B"); db.uncollect("C")
    assert db.collected() == []

    # 5. 分区榜独立入库：与综合热榜互不污染，分区内能选到自己的上一批
    db.save_batch("20260102000000",
                  [{"source": "bilibili", "title": "X", "rank": 9}], channel="游戏")
    db.save_batch("20260102002000",
                  [{"source": "bilibili", "title": "X", "rank": 2},
                   {"source": "bilibili", "title": "Y", "rank": 30}], channel="游戏")
    assert db.batches(1) == ["20260101001000"], db.batches(1)
    assert db.batches(1, "游戏") == ["20260102002000"], db.batches(1, "游戏")
    assert db.items_of("20260102000000") == [], "分区榜条目污染了综合热榜"
    assert api._pick_prev("20260102002000", "游戏") == "20260102000000"
    assert api._pick_prev("20260101002000") == "20260101001000"
    assert [r["title"] for r in Api._risen(
        [{"title": "X", "delta": 7}, {"title": "Y", "delta": -1},
         {"title": "Z", "delta": 0}])] == ["X"]

    # 6. 素材账本：只存链接与授权，按图片/视频分组导出，同 page_url 去重
    db.add_material({"platform": "pexels", "kind": "photo", "title": "夜间城市",
                     "author": "Ann", "author_url": "https://www.pexels.com/@ann",
                     "page_url": "https://www.pexels.com/photo/1",
                     "preview_url": "p.jpg", "file_url": "f.jpg",
                     "license": "Pexels License（免费商用）",
                     "width": 1920, "height": 1080})
    db.add_material({"platform": "pexels", "kind": "photo", "title": "夜间城市",
                     "author": "Ann", "page_url": "https://www.pexels.com/photo/1"})
    db.add_material({"platform": "pexels", "kind": "video", "title": "Pexels 视频 · 8s",
                     "author": "Bob", "page_url": "https://www.pexels.com/video/2",
                     "duration": 8, "width": 3840, "height": 2160,
                     "license": "Pexels License（免费商用）"})
    db.add_material({"platform": "ccmixter", "kind": "audio", "title": "Guitar Loop",
                     "author": "Cid", "page_url": "https://ccmixter.org/files/1",
                     "file_url": "https://ccmixter.org/content/1.mp3",
                     "license": "Noncommercial Sampling Plus",
                     "license_url": "http://creativecommons.org/licenses/nc-sampling+/1.0/"})
    assert len(db.materials()) == 3, db.materials()
    md2 = api.export_materials_md()
    assert md2.index("## 图片") < md2.index("## 视频") < md2.index("## 音乐"), md2
    assert "作者：Ann" in md2 and "原页：https://www.pexels.com/photo/1" in md2, md2
    assert "8s" in md2 and "3840×2160" in md2, md2
    assert "禁止商用" in md2 and "nc-sampling+" in md2, md2
    assert "ccMixter" in md2, md2
    db.remove_material("https://www.pexels.com/photo/1")
    assert len(db.materials()) == 2

    # 6b. 多源调度：没填 key 时只有 ccMixter 参与；填了才加对应源
    api2 = Api.__new__(Api)       # 纯逻辑，不碰真实数据目录
    api2.db = db
    names = [n for n, _ in api2._material_jobs("cat", "audio")]
    assert names == ["ccMixter"], names
    assert api2._material_jobs("cat", "photo") == [], "没 key 不该有图片源"
    assert api2.set_material_key("pexels", "k-test") is True
    assert api2.set_material_key("bogus", "x") is False
    st = api2.material_status()
    assert st["pexels"] is True and st["pixabay"] is False, st
    names = [n for n, _ in api2._material_jobs("cat", "all")]
    assert "Pexels" in names and "ccMixter" in names, names
    assert "Unsplash" not in names and "Jamendo" not in names, names

    # 7. 剪贴板（会覆盖当前剪贴板内容）
    assert copy_text("创作雷达自检"), "写入剪贴板失败"
    assert read_text() == "创作雷达自检", "读回内容不一致"

    print("自检全部通过：聚类 / 标签 / 入库 / 升温 / 收藏分组导出 / 分区榜 / 素材账本与多源调度 / 剪贴板")


if __name__ == "__main__":
    main()
