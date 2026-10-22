"""创作雷达 · 主程序。

pywebview 直接以 js_api 暴露方法给页面，不起本地 HTTP 服务。
"""

import importlib
import json
import os
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import webview

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from clip import copy_text  # noqa: E402
from db import Db  # noqa: E402

MODULES = {
    "baidu": "fetch_baidu",
    "bilibili": "fetch_bilibili",
    "weibo": "fetch_weibo",
    "zhihu": "fetch_zhihu",
}

# 领域关键词表：按顺序匹配，命中即停。想加词直接改这里。
TAGS = {
    "游戏": ["游戏", "原神", "王者", "英雄联盟", "LOL", "Steam", "主机", "米哈游", "黑猴",
             "影之刃", "电竞", "赛季", "玩家", "任天堂", "Switch", "宝可梦", "抽卡", "副本",
             "开服", "手游", "端游", "吃鸡", "崩坏", "鸣潮", "绝区零", "黑神话", "DLC"],
    "动漫": ["动漫", "番剧", "二次元", "新番", "声优", "手办", "cos", "鬼灭", "咒术", "海贼",
             "火影", "进击的巨人", "宫崎骏", "剧场版", "同人", "漫展", "连载", "动画"],
    "影视": ["电影", "电视剧", "票房", "导演", "演员", "预告", "综艺", "主演", "开机", "片花",
             "影评", "网剧", "定档", "点映", "首映", "杀青", "剧组", "番外", "短剧", "大秀"],
    "科技": ["AI", "人工智能", "芯片", "苹果", "华为", "手机", "发布会", "英伟达", "机器人",
             "大模型", "系统", "显卡", "骁龙", "小米", "卫星", "火箭", "量子", "算力", "App",
             "网站", "微信", "账号", "防沉迷", "软件", "漏洞", "开源", "浏览器", "数据"],
    "娱乐": ["明星", "恋情", "结婚", "离婚", "演唱会", "出道", "塌房", "官宣", "娱乐圈",
             "粉丝", "绯闻", "选秀", "偶像", "八卦", "脱粉", "拍戏", "歌手", "超女",
             "快男", "剧组", "片酬", "绯闻", "恋爱", "分手"],
    "体育": ["比赛", "球队", "球员", "冠军", "联赛", "世界杯", "奥运", "NBA", "CBA", "足球",
             "篮球", "乒乓", "田径", "夺冠", "国足", "网球", "马拉松"],
    "财经": ["股市", "A股", "基金", "房价", "经济", "银行", "利率", "汇率", "黄金", "比特币",
             "裁员", "上市", "融资", "财报", "物价", "油价", "降息", "存款",
             "美股", "纳指", "道指", "大盘", "涨停", "跌超", "赚钱", "利润", "营收"],
    "社会": ["事故", "警方", "通报", "法院", "政策", "医保", "教育", "高考", "就业", "工资",
             "判刑", "诈骗", "火灾", "地震", "救援", "立法", "社保", "退休", "纪委",
             "回应", "曝光", "调查", "致歉", "赔偿", "起诉", "判决", "处罚", "整治",
             "遇难", "身亡", "失踪", "抓获", "涉嫌", "官方", "通报批评", "辟谣",
             "出圈", "商场", "地铁", "违章", "景区", "小区", "街道"],
    "生活": ["减肥", "美食", "旅游", "天气", "宠物", "家庭", "婚礼", "健康", "房租", "育儿",
             "买菜", "睡眠", "养生", "出行", "假期", "露营", "装修", "快递",
             "消费", "餐饮", "超市", "饮料", "入座", "逛街", "外卖"],
}

# 分区专属榜：(源, 参数)。B站参数是 rid，微博是 band 名，百度是 tab 名。
# 实测 2026-10-22：B站除 rid=71（综艺）外均有 60-97 条；百度只有 finance/sports 是文字榜。
CHANNELS = {
    "游戏": [("bilibili", 4)],
    "动漫": [("bilibili", 1)],
    "影视": [("bilibili", 181), ("bilibili", 23)],
    "科技": [("bilibili", 188), ("bilibili", 36)],
    "娱乐": [("bilibili", 5), ("weibo", "ent")],
    "体育": [("bilibili", 234), ("baidu", "sports")],
    "财经": [("baidu", "finance")],
    "生活": [("bilibili", 160), ("bilibili", 211)],
}
CHANNEL_TTL = 600  # 分区榜内存缓存 10 分钟
CHANNEL_LIMIT = 30  # 每个榜最多取前 30 条

# 标签聚合时排除的通用词（这些不适合当作品分类）
TAG_STOP = {
    "游戏", "手游", "单机", "网游", "端游", "攻略", "实况", "解说", "搞笑", "日常",
    "原创", "剪辑", "动画", "二次元", "杂谈", "挑战", "测评", "开箱", "直播", "录播",
    "整活", "高能", "名场面", "视频", "推荐", "手机游戏", "单机游戏", "网络游戏",
    "电子竞技", "桌游棋牌", "音游", "影视剪辑", "影视杂谈", "动漫杂谈", "短片",
}

SIM_THRESHOLD = 0.55  # 标题字符集 Jaccard 阈值，调高更严格


def data_path() -> str:
    """便携优先：程序同目录下的 data\\radar.db 可写就用它（U 盘带走全部设置与历史）。

    不可写（U 盘写保护、安装在 Program Files 等）才退回 %LOCALAPPDATA%\\创作雷达。
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = BASE
    portable = os.path.join(base, "data")
    try:
        os.makedirs(portable, exist_ok=True)
        probe = os.path.join(portable, ".writetest")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return os.path.join(portable, "radar.db")
    except OSError:
        pass
    d = os.path.join(os.environ.get("LOCALAPPDATA") or base, "创作雷达")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "radar.db")


def resource(rel: str) -> str:
    return os.path.join(getattr(sys, "_MEIPASS", BASE), rel)


def tag_of(title: str) -> str:
    for tag, kws in TAGS.items():
        if any(k in title for k in kws):
            return tag
    return "综合"


def similarity(a: str, b: str) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def build_clusters(items: list[dict]) -> list[list[int]]:
    """跨源同题归并：只在不同源之间比，用并查集。"""
    n = len(items)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if items[i]["source"] == items[j]["source"]:
                continue
            if similarity(items[i]["title"], items[j]["title"]) >= SIM_THRESHOLD:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return [g for g in groups.values() if len({items[i]["source"] for i in g}) >= 2]


class Api:
    def __init__(self):
        self.db = Db(data_path())
        self._lock = threading.Lock()
        self._cache: dict[str, dict] = {}
        self._ch_cache: dict[str, tuple] = {}  # tag -> (时间戳, items)
        self._batch: str = ""

    # ---------- 抓取 ----------

    def _grab(self, name: str):
        try:
            mod = importlib.import_module(MODULES[name])
            return name, mod.fetch(), ""
        except Exception as e:  # 单源失败不影响其他源
            return name, [], f"{type(e).__name__}: {e}"

    def refresh(self) -> dict:
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "正在刷新中"}
        try:
            import datetime

            batch = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            raw, status = [], {}
            with ThreadPoolExecutor(max_workers=4) as ex:
                for name, items, err in ex.map(self._grab, MODULES):
                    status[name] = {"ok": not err and bool(items),
                                    "count": len(items), "error": err}
                    for it in items:
                        raw.append({"source": it.source, "title": it.title,
                                    "url": it.url, "rank": it.rank,
                                    "hot": it.hot, "hot_text": it.hot_text})
            if not raw:
                return {"ok": False, "error": "四个源都没拿到数据，检查网络",
                        "sources": status}
            self.db.save_batch(batch, raw)
            self.db.cleanup()
            self._batch = batch
            import datetime as _dt

            return {"ok": True, **self._view(batch), "sources": status,
                    "fetched_at": _dt.datetime.now().isoformat(timespec="seconds")}
        finally:
            self._lock.release()

    def state(self) -> dict:
        batches = self.db.batches(1)
        if not batches:
            return {"ok": True, "empty": True, "items": [], "clusters": [],
                    "sources": {}, "fetched_at": self.db.last_fetch_time()}
        return {"ok": True, **self._view(batches[0]),
                "sources": {}, "fetched_at": self.db.last_fetch_time()}

    # ---------- 组装视图 ----------

    def _pick_prev(self, batch: str, channel: str = "") -> str:
        """选对比基准：至少 10 分钟前最近的一批；不够久就退上一批。

        相邻两次抓取隔得太近，排名几乎不变，升温榜会全空。
        channel 分开算：综合热榜比综合热榜，分区榜比同分区的上一次。
        """
        import datetime as _dt

        try:
            cur = _dt.datetime.strptime(batch, "%Y%m%d%H%M%S")
        except ValueError:
            return ""
        others = [b for b in self.db.batches(30, channel) if b != batch]
        for b in others:
            try:
                gap = (cur - _dt.datetime.strptime(b, "%Y%m%d%H%M%S")).total_seconds()
            except ValueError:
                continue
            if gap >= 600:
                return b
        return others[0] if others else ""

    def _view(self, batch: str) -> dict:
        if batch in self._cache:
            return self._cache[batch]

        items = self.db.items_of(batch)
        prev = {}
        prev_batch = self._pick_prev(batch)
        if prev_batch:
            prev = {(i["source"], i["title"]): i["rank"]
                    for i in self.db.items_of(prev_batch)}

        for it in items:
            it["tag"] = tag_of(it["title"])
            p = prev.get((it["source"], it["title"]))
            it["prev_rank"] = p
            it["delta"] = (p - it["rank"]) if p else 0

        clusters = build_clusters(items)
        for gi, group in enumerate(clusters):
            for idx in group:
                items[idx]["cluster"] = gi
            sources = [items[i]["source"] for i in group]
            for idx in group:
                items[idx]["platforms"] = sources

        rising = sorted(
            [i for i in items if i.get("delta", 0) > 0],
            key=lambda x: -x["delta"],
        )[:40]

        data = {
            "items": items,
            "clusters": [[items[i]["title"] for i in g] for g in clusters],
            "clusterIdx": clusters,
            "rising": rising,
            "batch": batch,
        }
        self._cache = {batch: data}
        return data


    # ---------- 分区专属榜 ----------

    def _one_channel(self, spec):
        src, arg = spec
        mod = importlib.import_module(MODULES[src])
        if src == "bilibili":
            return mod.fetch_rank(arg)
        if src == "weibo":
            return mod.fetch_band(arg)
        return mod.fetch_tab(arg)

    def channel(self, tag: str) -> dict:
        """按需抓某分区的专属榜，内存缓存 10 分钟。

        抓到的榜当场落库（channel=分区名），下一轮才有升温基准。
        """
        specs = CHANNELS.get(tag) or []
        if not specs:
            return {"ok": True, "tag": tag, "items": [], "count": 0, "rising": [],
                    "note": "该分区没有专属榜，只显示综合热榜命中条目"}
        hit = self._ch_cache.get(tag)
        if hit and time.time() - hit[0] < CHANNEL_TTL:
            return {"ok": True, "tag": tag, "items": hit[1],
                    "count": len(hit[1]), "hot_tags": hit[2], "cached": True,
                    "rising": self._risen(hit[1])}

        items, errors = [], []
        with ThreadPoolExecutor(max_workers=3) as ex:
            tasks = [(ex.submit(self._one_channel, spec), spec) for spec in specs]
            for fut, spec in tasks:
                try:
                    for it in (fut.result() or [])[:CHANNEL_LIMIT]:
                        items.append({
                            "source": it.source, "title": it.title, "url": it.url,
                            "rank": it.rank, "hot": it.hot, "hot_text": it.hot_text,
                            "tag": tag, "from_channel": True,
                            "sub": getattr(it, "sub", "") or "",
                        })
                except Exception as e:
                    errors.append(f"{spec[0]} {spec[1]}: {type(e).__name__}")
        seen, uniq = set(), []
        for it in items:
            if it["title"] in seen:
                continue
            seen.add(it["title"])
            uniq.append(it)

        # 批量取 B站视频标签 → 按作品/游戏名聚合
        bvids = []
        for it in uniq:
            url = it.get("url") or ""
            if it.get("source") == "bilibili" and "/video/" in url:
                bvids.append(url.rsplit("/", 1)[-1])
        tagmap = self._tags_for(bvids) if bvids else {}
        for it in uniq:
            url = it.get("url") or ""
            bv = url.rsplit("/", 1)[-1] if "/video/" in url else ""
            it["tags"] = tagmap.get(bv, [])

        counts: dict[str, int] = {}
        for it in uniq:
            for t in it.get("tags") or []:
                if 2 <= len(t) <= 12 and t not in TAG_STOP:
                    counts[t] = counts.get(t, 0) + 1
        hot_tags = [t for t, n in sorted(counts.items(), key=lambda kv: -kv[1])
                    if n >= 2][:14]

        # P1：分区榜落库，下一轮点同一分区才有排名对比
        import datetime as _dt

        cbatch = _dt.datetime.now().strftime("%Y%m%d%H%M%S")
        self.db.save_batch(cbatch, uniq, channel=tag)
        self.db.cleanup()
        prev_batch = self._pick_prev(cbatch, tag)
        prev = {}
        if prev_batch:
            prev = {(i["source"], i["title"]): i["rank"]
                    for i in self.db.items_of(prev_batch, tag)}
        for it in uniq:
            p = prev.get((it["source"], it["title"]))
            it["prev_rank"] = p
            it["delta"] = (p - it["rank"]) if p else 0

        self._ch_cache[tag] = (time.time(), uniq, hot_tags)
        return {"ok": True, "tag": tag, "items": uniq, "count": len(uniq),
                "hot_tags": hot_tags, "errors": errors, "rising": self._risen(uniq)}

    @staticmethod
    def _risen(items: list[dict]) -> list[dict]:
        """分区榜里排名上升的条目（最多 40 条）。"""
        return sorted([i for i in items if i.get("delta", 0) > 0],
                      key=lambda x: -x["delta"])[:40]

    def _tags_for(self, bvids: list[str]) -> dict:
        """并发取标签，最多 8 路。"""
        mod = importlib.import_module("fetch_bilibili")
        out = {}

        def one(bv):
            return bv, mod.fetch_tags(bv)

        with ThreadPoolExecutor(max_workers=8) as ex:
            for bv, tags in ex.map(one, bvids):
                out[bv] = tags
        return out

    # ---------- 收藏 / 工具 ----------

    def collect(self, item: dict) -> bool:
        self.db.collect(item)
        return True

    def uncollect(self, title: str) -> bool:
        self.db.uncollect(title)
        return True

    def collected(self) -> list[dict]:
        return self.db.collected()

    def copy(self, text: str) -> bool:
        return copy_text(text)

    def settings(self) -> dict:
        return self.db.settings()

    def set_setting(self, key: str, value: str) -> bool:
        self.db.set_setting(str(key), str(value))
        return True

    # ---------- 素材库（Pexels / Pixabay / Unsplash / ccMixter / Jamendo） ----------

    KEY_FIELDS = {"pexels": "pexels_key", "pixabay": "pixabay_key",
                  "unsplash": "unsplash_key", "jamendo": "jamendo_client_id"}

    def material_keys(self) -> dict:
        s = self.db.settings()
        return {src: (s.get(field) or "").strip()
                for src, field in self.KEY_FIELDS.items()}

    def material_status(self) -> dict:
        k = self.material_keys()
        return {**{src: bool(v) for src, v in k.items()}, "has_key": any(k.values())}

    def set_material_key(self, source: str, key: str) -> bool:
        field = self.KEY_FIELDS.get(source)
        if not field:
            return False
        self.db.set_setting(field, (key or "").strip())
        return True

    def _material_jobs(self, q: str, kind: str) -> list[tuple[str, object]]:
        """按 kind 与已填的 key 组装要跑的源。ccMixter 免 key 永远参与。"""
        import fetch_music
        import fetch_pexels
        import fetch_pixabay
        import fetch_unsplash

        k = self.material_keys()
        photo_on = kind in ("all", "photo")
        video_on = kind in ("all", "video")
        audio_on = kind in ("all", "audio")
        jobs: list[tuple[str, object]] = []

        if photo_on or video_on:
            if k["pexels"]:
                if photo_on:
                    jobs.append(("Pexels", lambda: fetch_pexels.search_photos(k["pexels"], q)))
                if video_on:
                    jobs.append(("Pexels", lambda: fetch_pexels.search_videos(k["pexels"], q)))
            if k["pixabay"]:
                if photo_on:
                    jobs.append(("Pixabay", lambda: fetch_pixabay.search_photos(k["pixabay"], q)))
                if video_on:
                    jobs.append(("Pixabay", lambda: fetch_pixabay.search_videos(k["pixabay"], q)))
            if photo_on and k["unsplash"]:
                jobs.append(("Unsplash", lambda: fetch_unsplash.search_photos(k["unsplash"], q)))
        if audio_on:
            jobs.append(("ccMixter", lambda: fetch_music.search_ccmixter(q)))
            if k["jamendo"]:
                jobs.append(("Jamendo", lambda: fetch_music.search_jamendo(k["jamendo"], q)))
        return jobs

    def material_search(self, query: str, kind: str = "all") -> dict:
        """并行搜所有可用源；kind=photo/video/audio/all。"""
        from concurrent.futures import as_completed

        q = (query or "").strip()
        if not q:
            return {"ok": True, "items": [], "note": "输入关键词再搜"}
        jobs = self._material_jobs(q, kind)
        if not jobs:
            return {"ok": False, "items": [], "need_key": True,
                    "note": "图片/视频需要 Pexels、Pixabay 或 Unsplash 任一 key；"
                            "音乐 ccMixter 免 key，切到「音乐」就能搜"}

        items, sources, errors = [], {}, []
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(fn): name for name, fn in jobs}
            for fut in as_completed(futs):
                name = futs[fut]
                try:
                    got = fut.result() or []
                    items += got
                    sources[name] = sources.get(name, 0) + len(got)
                except Exception as e:
                    msg = str(e)[:90]
                    errors.append(f"{name}: {msg}")
                    sources[name] = f"失败：{msg}"
        return {"ok": True, "items": items, "count": len(items), "query": q,
                "kind": kind, "sources": sources, "errors": errors}

    def collect_material(self, item: dict) -> bool:
        self.db.add_material(item)
        return True

    def uncollect_material(self, page_url: str) -> bool:
        self.db.remove_material(page_url)
        return True

    def materials(self) -> list[dict]:
        return self.db.materials()

    def export_materials_md(self) -> str:
        """素材账本：按图片/视频/音乐分组，带平台、作者、原页、直链与授权。"""
        rows = self.db.materials()
        if not rows:
            return ""
        import datetime

        names = {"photo": "图片", "video": "视频", "audio": "音乐"}
        plat = {"pexels": "Pexels", "pixabay": "Pixabay", "unsplash": "Unsplash",
                "ccmixter": "ccMixter", "jamendo": "Jamendo"}
        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(names.get(r["kind"], "其它"), []).append(r)

        today = datetime.date.today().isoformat()
        lines = [f"# 素材账本 · {today}", "",
                 f"> 共 {len(rows)} 项 · 导出 {today}", ""]
        for kind in ("图片", "视频", "音乐", "其它"):
            items = groups.get(kind)
            if not items:
                continue
            lines.append(f"## {kind}（{len(items)}）")
            lines.append("")
            if kind == "音乐":
                lines.append("> ⚠ 音乐多为 Creative Commons 变体，注意 NC（禁止商用）限制；"
                             "逐条看下面的「授权」链接。")
                lines.append("")
            for r in items:
                size = (f"{r['width']}×{r['height']}" if r.get("width") else "")
                if r.get("duration"):
                    size += f" · {r['duration']}s"
                src = plat.get(r.get("platform"), r.get("platform") or "")
                head = f"- **{r['title']}**"
                if size:
                    head += f" · {size}"
                if src:
                    head += f" · {src}"
                lines.append(head)
                if r.get("author"):
                    lines.append(f"  作者：{r['author']}" + (f"（{r['author_url']}）"
                                                         if r.get("author_url") else ""))
                if r.get("page_url"):
                    lines.append(f"  原页：{r['page_url']}")
                if r.get("file_url"):
                    lines.append(f"  文件：{r['file_url']}")
                lic = r.get("license") or "未记录"
                if r.get("license_url"):
                    lic += f" · {r['license_url']}"
                lines.append(f"  授权：{lic}")
                lines.append(f"  收录：{(r.get('added_at') or '')[:10]}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def open_url(self, url: str) -> bool:
        if url:
            webbrowser.open(url)
            return True
        return False

    def export_md(self) -> str:
        """按领域分区把选题夹分组导出，分区内保持收藏时间倒序。"""
        rows = self.db.collected()
        if not rows:
            return ""
        import datetime

        name = {"baidu": "百度", "bilibili": "B站", "weibo": "微博", "zhihu": "知乎"}
        order = list(TAGS) + ["综合", ""]

        def rank(t: str) -> int:
            return order.index(t) if t in order else len(order)

        groups: dict[str, list[dict]] = {}
        for r in rows:
            groups.setdefault(r.get("tag") or "", []).append(r)

        lines = [f"# 选题夹 · {datetime.date.today().isoformat()}", ""]
        for tag in sorted(groups, key=rank):
            lines.append(f"## {tag or '未分类'}")
            lines.append("")
            for r in groups[tag]:
                src = name.get(r["source"], r["source"] or "来源未知")
                extra = f" · {r['hot_text']}" if r.get("hot_text") else ""
                lines.append(f"- **[{src}]** {r['title']}{extra}")
                if r.get("url"):
                    lines.append(f"  {r['url']}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def main():
    api = Api()
    w, h = 1280, 820
    try:  # 投影/小屏自适应：教室常见 1366×768
        scr = webview.screens[0]
        w = max(960, min(1280, int(scr.width) - 80))
        h = max(600, min(820, int(scr.height) - 80))
    except Exception:
        pass
    webview.create_window(
        "创作雷达",
        url=resource(os.path.join("web", "index.html")),
        js_api=api,
        width=w,
        height=h,
        min_size=(900, 560),
        background_color="#fffaf5",
    )
    webview.start()


if __name__ == "__main__":
    main()
