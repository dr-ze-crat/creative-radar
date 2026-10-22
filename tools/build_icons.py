"""把 assets/icons 下的 Tabler SVG 拼成可直接注入页面的 sprite（web/icons.js）。

用法：python tools/build_icons.py
图标来源：Tabler Icons 3.49.0，MIT 许可，可商用。
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "icons")
OUT = os.path.join(ROOT, "web", "icons.js")


def main():
    symbols = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".svg"):
            continue
        name = f[:-4]
        with open(os.path.join(SRC, f), encoding="utf-8") as fh:
            txt = fh.read()
        m = re.search(r"<svg[^>]*>(.*)</svg>", txt, re.S)
        if not m:
            print(f"跳过（无 svg 内容）: {f}")
            continue
        inner = m.group(1).strip()
        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{inner}</symbol>')

    sprite = (
        '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" '
        'style="position:absolute;width:0;height:0;overflow:hidden">'
        + "".join(symbols)
        + "</svg>"
    )
    js = (
        "/* 由 tools/build_icons.py 生成，勿手改 */\n"
        "const __SPRITE = " + json.dumps(sprite, ensure_ascii=False) + ";\n"
        "document.addEventListener('DOMContentLoaded', () => "
        "document.body.insertAdjacentHTML('afterbegin', __SPRITE));\n"
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(js)
    print(f"已生成 {OUT}，{len(symbols)} 个图标，{len(js)} 字节")


if __name__ == "__main__":
    main()
