"""生成「创作雷达」应用图标：透明底 + 橙色渐变雷达。

输出：
    assets/appicon.ico   多尺寸（16/24/32/48/64/128/256），打包用
    assets/appicon.png   1024 预览
    web/appicon.png      128，界面侧栏用

    python tools/make_icon.py

设计约束：
    - 透明底，图形自身带颜色，放在浅色/深色桌面都看得见；
    - 环宽 ≥ 0.03S，再细在 16px 下会消失；
    - 热点圆点落在两环之间，压到环上会显脏。
"""

import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024  # 超采样画布，最后降采样得到抗锯齿

# 线条渐变：左上浅橙 → 右下深橙（比原 #ff7a45 略深，保证白底上对比度）
C1 = (255, 145, 90)
C2 = (244, 88, 30)
BEAM = (255, 106, 61, 64)  # 扫描扇形：半透明橙


def _mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def gradient(size):
    """对角渐变，先小图算再放大，避免百万次逐像素循环。"""
    small = 128
    g = Image.new("RGB", (small, small))
    px = g.load()
    for y in range(small):
        for x in range(small):
            t = (x + y) / (2 * (small - 1))
            px[x, y] = _mix(C1, C2, t)
    return g.resize((size, size), Image.BICUBIC).convert("RGBA")


def main():
    cx = cy = S // 2
    outer = int(S * 0.395)   # 外环半径（无底后可放大，撑满画布）
    inner = int(S * 0.215)   # 内环半径
    ring_w = int(S * 0.038)
    dot = int(S * 0.062)

    # 1) 线条先画成白色 alpha 遮罩
    shape = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(shape)
    W = (255, 255, 255, 255)
    for r in (inner, outer):
        d.arc([cx - r, cy - r, cx + r, cy + r], 0, 360, fill=W, width=ring_w)
    ang = math.radians(-46)
    d.line([(cx, cy), (cx + outer * math.cos(ang), cy + outer * math.sin(ang))],
           fill=W, width=int(S * 0.022))
    d.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=W)
    for r, deg in ((int(outer * 0.74), -70), (int(outer * 0.70), -22)):
        a = math.radians(deg)
        hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        hr = int(S * 0.040)
        d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=W)

    mask = shape.split()[3]

    # 2) 扇形光束（半透明，垫在下面）
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    beam = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(beam).pieslice(
        [cx - outer, cy - outer, cx + outer, cy + outer],
        start=-80, end=-14, fill=BEAM,
    )
    out = Image.alpha_composite(out, beam)

    # 3) 渐变填充线条
    colored = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    colored.paste(gradient(S), (0, 0), mask)
    out = Image.alpha_composite(out, colored)

    # ---- 输出 ----
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "web"), exist_ok=True)

    out.resize((1024, 1024), Image.LANCZOS).save(
        os.path.join(ROOT, "assets", "appicon.png"))
    out.resize((128, 128), Image.LANCZOS).save(
        os.path.join(ROOT, "web", "appicon.png"))
    out.save(os.path.join(ROOT, "assets", "appicon.ico"), format="ICO",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                    (128, 128), (256, 256)])

    # 小尺寸预览，便于肉眼检查（跑完可删）
    for px in (32, 48):
        out.resize((px, px), Image.LANCZOS).save(
            os.path.join(ROOT, "assets", f"_preview{px}.png"))
    print("已生成透明底图标：assets/appicon.ico、appicon.png、web/appicon.png")


if __name__ == "__main__":
    main()
