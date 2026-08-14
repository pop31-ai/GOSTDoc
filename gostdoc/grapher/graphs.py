"""Построение схем: UML-классов и графа вызовов (ГОСТ 19.701).

Схемы генерируются в Graphviz DOT. Если `dot` не установлен,
генерация схем пропускается без сбоя.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..parser.model import Project

try:
    import graphviz  # type: ignore
except ImportError:  # pragma: no cover
    graphviz = None


def _dot_available() -> bool:
    return shutil.which("dot") is not None


def _simple() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def _fallback(out_dir: Path):
    """Импорт простого рендера Pillow (используется без Graphviz)."""
    from .simple import class_diagram as cd
    from .simple import call_graph as cg
    from .simple import flowcharts as fc
    return cd, cg, fc


def _gost_node_style():
    return dict(shape="box", fontname="Arial", fontsize="10", color="#000000")


def class_diagram(proj: Project, out_dir: Path) -> str | None:
    """UML-диаграмма классов. Возвращает путь к PNG или None."""
    if graphviz is not None and _dot_available():
        return _class_diagram_dot(proj, out_dir)
    if _simple():
        cd, _cg, _fc = _fallback(out_dir)
        return cd(proj, out_dir)
    return None


def _class_diagram_dot(proj: Project, out_dir: Path) -> str | None:
    if not proj.classes:
        return None
    g = graphviz.Digraph("classes", format="png")
    g.attr(rankdir="TB", splines="ortho", nodesep="0.3", ranksep="0.35")
    for cls in proj.classes:
        methods = "\n".join(f"{m.return_type} {m.name}({', '.join(m.params)})"
                            for m in cls.methods)
        fields = "\n".join(cls.fields) if cls.fields else ""
        label = f"<<table border='0' cellborder='1' cellspacing='0' cellpadding='4'>" \
                f"<tr><td bgcolor='#DDEEFF'><b>{cls.name}</b></td></tr>" \
                f"<tr><td align='left'>{methods.replace(chr(10), '<br/>')}</td></tr>" \
                f"<tr><td align='left'>{fields.replace(chr(10), '<br/>')}</td></tr>" \
                f"</table>"
        g.node(cls.name, label=label, shape="plaintext")
    for cls in proj.classes:
        if cls.base:
            g.edge(cls.base, cls.name, arrowhead="empty", label="  наследует")
    out = out_dir / "classes"
    g.render(str(out), cleanup=True)
    return str(out) + ".png"


def call_graph(proj: Project, out_dir: Path) -> str | None:
    """Граф вызовов функций и методов. Возвращает путь к PNG или None."""
    if graphviz is not None and _dot_available():
        return _call_graph_dot(proj, out_dir)
    if _simple():
        _cd, cg, _fc = _fallback(out_dir)
        return cg(proj, out_dir)
    return None


def _call_graph_dot(proj: Project, out_dir: Path) -> str | None:
    if not proj.call_edges:
        return None
    g = graphviz.Digraph("calls", format="png")
    g.attr(rankdir="LR", nodesep="0.25", ranksep="0.5")
    names = {f.name for f in proj.all_functions()}
    for n in names:
        g.node(n, shape="box", style="rounded", fontname="Arial", fontsize="10")
    for src, dst in proj.call_edges:
        g.edge(src, dst)
    out = out_dir / "calls"
    g.render(str(out), cleanup=True)
    return str(out) + ".png"


def flowcharts(proj: Project, out_dir: Path) -> dict[str, str]:
    """Блок-схемы функций по ГОСТ 19.701 (старт / вызовы / конец)."""
    if graphviz is not None and _dot_available():
        return _flowcharts_dot(proj, out_dir)
    if _simple():
        _cd, _cg, fc = _fallback(out_dir)
        return fc(proj, out_dir)
    return {}


def _flowcharts_dot(proj: Project, out_dir: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    for f in proj.all_functions():
        if not f.calls:
            continue
        g = graphviz.Digraph(f.name, format="png")
        g.attr(rankdir="TB", nodesep="0.3", ranksep="0.35", margin="0.1")
        g.node("start", label="Начало", shape="ellipse")
        prev = "start"
        for i, c in enumerate(f.calls):
            node = f"c{i}"
            g.node(node, label=c, shape="box")
            g.edge(prev, node)
            prev = node
        g.node("end", label="Конец", shape="ellipse")
        g.edge(prev, "end")
        out = out_dir / f"flow_{f.name}"
        g.render(str(out), cleanup=True)
        results[f.name] = str(out) + ".png"
    return results
