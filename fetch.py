"""抓取入口。命令行单独验证某一源：

    python fetch.py baidu
    python fetch.py all
"""

import importlib
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8")

SOURCES = {
    "baidu": "fetch_baidu",
    "bilibili": "fetch_bilibili",
    "weibo": "fetch_weibo",
    "zhihu": "fetch_zhihu",
}


def run_one(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(SOURCES[name])
        items = mod.fetch()
        if not items:
            return False, f"[{name}] 返回 0 条，接口可能改版"
        lines = [f"[{name}] {len(items)} 条"]
        for it in items[:8]:
            extra = it.hot_text or (str(it.hot) if it.hot else "")
            lines.append(f"  {it.rank:>2}. {it.title}   ({extra})")
        return True, "\n".join(lines)
    except Exception as e:
        return False, f"[{name}] 失败：{type(e).__name__}: {e}\n{traceback.format_exc(limit=2)}"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(SOURCES) if target == "all" else [target]
    ok = 0
    for n in names:
        success, msg = run_one(n)
        ok += success
        print(msg)
        print("-" * 60)
    print(f"成功 {ok}/{len(names)} 个源")


if __name__ == "__main__":
    main()
