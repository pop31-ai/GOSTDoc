"""Собственный рендер схем на Pillow (без Graphviz).

Используется как fallback, чтобы схемы генерировались всегда:
диаграмма классов, граф вызовов, блок-схемы по ГОСТ 19.701.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..parser.model import Project

_FONT_PATH = "C:/Windows/Fonts/arial.ttf"
_BG = (255, 255, 255)
_LINE = (0, 0, 0)
_BOX = (255, 255, 255)
_HEAD = (190, 220, 245)


def _font(size: int):
    try:
        return ImageFont.truetype(_FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _text_wrap(text: str, font, max_w: int) -> list[str]:
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if _text_size(draw, test, font)[0] <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw_box(draw, x, y, w, h, lines, font, head_lines=0, fill=_BOX):
    draw.rectangle([x, y, x + w, y + h], outline=_LINE, fill=fill, width=2)
    for i, line in enumerate(lines):
        tw, th = _text_size(draw, line, font)
        tx = x + (w - tw) // 2
        ty = y + head_lines * 18 + 8 + i * 18
        draw.text((tx, ty), line, font=font, fill=_LINE)


def _arrow(draw, x1, y1, x2, y2):
    draw.line([x1, y1, x2, y2], fill=_LINE, width=2)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    a = 8
    for da in (0.45, -0.45):
        draw.line([x2, y2,
                   x2 - a * math.cos(ang - da), y2 - a * math.sin(ang - da)],
                  fill=_LINE, width=2)


def class_diagram(proj: Project, out_dir: Path) -> str | None:
    """Диаграмма классов. Возвращает путь к PNG или None."""
    if not proj.classes:
        return None
    font = _font(11)
    bw, bh = 220, 40
    cols, row_h = 1, 260
    for cls in proj.classes:
        n = max(1, len(cls.methods)) + max(1, len(cls.fields)) + 1
        row_h = max(row_h, 40 + n * 18)
    w = bw * cols + 80
    h = row_h * max(1, len(proj.classes)) + 80
    img = Image.new("RGB", (w, h), _BG)
    draw = ImageDraw.Draw(img)

    for i, cls in enumerate(proj.classes):
        x = 40
        y = 40 + i * row_h
        head = cls.name + (f" : {cls.base}" if cls.base else "")
        lines = _text_wrap(head, font, bw - 12)
        n_items = len(lines) + len(cls.methods) + len(cls.fields) + 1
        box_h = n_items * 18 + 16
        _draw_box(draw, x, y, bw, box_h, lines, font, fill=_HEAD)
        yy = y + len(lines) * 18 + 12
        for m in cls.methods:
            _draw_box(draw, x, yy, bw, 20, [f"{m.return_type} {m.name}()".strip()], font)
            yy += 20
        for f_ in cls.fields:
            _draw_box(draw, x, yy, bw, 20, [_text_wrap(f_, font, bw - 12)[0]], font)
            yy += 20

    # связи наследования
    pos = {c.name: (40, 40 + i * row_h) for i, c in enumerate(proj.classes)}
    for cls in proj.classes:
        if cls.base and cls.base in pos:
            bx, by = pos[cls.base]
            x, y = pos[cls.name]
            _arrow(draw, bx + bw // 2, by + 12, x + bw // 2, y)

    out = out_dir / "classes"
    img.save(str(out) + ".png")
    return str(out) + ".png"


def call_graph(proj: Project, out_dir: Path) -> str | None:
    """Граф вызовов: вершины-функции, рёбра-вызовы."""
    if not proj.call_edges:
        return None
    font = _font(10)
    names = sorted({f.name for f in proj.all_functions()})
    bw, bh, gap = 150, 34, 18
    w = bw * 3 + gap * 2 + 60
    rows = max(1, (len(names) + 2) // 3)
    h = rows * (bh + 26) + 40
    img = Image.new("RGB", (w, h), _BG)
    draw = ImageDraw.Draw(img)
    pos: dict[str, tuple[int, int]] = {}
    for i, n in enumerate(names):
        col, row = i % 3, i // 3
        x = 30 + col * (bw + gap)
        y = 20 + row * (bh + 26)
        pos[n] = (x, y)
        lines = _text_wrap(n, font, bw - 12)
        _draw_box(draw, x, y, bw, bh, lines, font)
    for src, dst in proj.call_edges:
        if src in pos and dst in pos:
            x1, y1 = pos[src][0] + bw, pos[src][1] + bh // 2
            x2, y2 = pos[dst][0], pos[dst][1] + bh // 2
            _arrow(draw, x1, y1, x2, y2)
    out = out_dir / "calls"
    img.save(str(out) + ".png")
    return str(out) + ".png"


def flowchart(name: str, calls: list[str], out_dir: Path) -> str | None:
    """Блок-схема функции по ГОСТ 19.701: Начало -> вызовы -> Конец."""
    if not calls:
        return None
    font = _font(11)
    bw, bh, gap = 180, 36, 26
    w = bw + 120
    h = (len(calls) + 2) * (bh + gap) + 40
    img = Image.new("RGB", (w, h), _BG)
    draw = ImageDraw.Draw(img)
    x = (w - bw) // 2

    def ellipse(y, text, w_=120):
        ex = (w - w_) // 2
        lines = _text_wrap(text, font, w_ - 14)
        draw.ellipse([ex, y, ex + w_, y + bh], outline=_LINE, width=2)
        for i, ln in enumerate(lines):
            tw, th = _text_size(draw, ln, font)
            draw.text((ex + (w_ - tw) // 2, y + 10 + i * 16), ln, font=font, fill=_LINE)
        return w_

    y = 20
    ellipse(y, "Начало", 110)
    y += bh + gap
    prev = (x + bw // 2, y - gap)
    for c in calls:
        lines = _text_wrap(c, font, bw - 12)
        _draw_box(draw, x, y, bw, bh, lines, font)
        _arrow(draw, prev[0], prev[1] + bh // 2, x + bw // 2, y - gap // 2 - 4)
        y += bh + gap
        prev = (x + bw // 2, y - gap)
    ellipse(y, "Конец", 110)
    _arrow(draw, prev[0], prev[1] + bh // 2, w // 2, y)
    out = out_dir / f"flow_{name}"
    img.save(str(out) + ".png")
    return str(out) + ".png"


def flowcharts(proj: Project, out_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in proj.all_functions():
        if f.calls:
            out[f.name] = flowchart(f.name, f.calls, out_dir)
    return out
