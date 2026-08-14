"""Тесты собственного рендера схем на Pillow (fallback без Graphviz)."""

from pathlib import Path

from gostdoc.grapher.graphs import call_graph, class_diagram, flowcharts
from gostdoc.parser.cpp_parser import parse_project


def test_pillow_diagrams(tmp_path: Path):
    proj = parse_project(Path("examples/sample"))
    cls = class_diagram(proj, tmp_path)
    cg = call_graph(proj, tmp_path)
    fc = flowcharts(proj, tmp_path)
    if cls:
        assert Path(cls).exists() and Path(cls).stat().st_size > 0
    if cg:
        assert Path(cg).exists()
    if fc:
        for p in fc.values():
            assert Path(p).exists()


def test_class_diagram_names(tmp_path: Path):
    from gostdoc.grapher.simple import class_diagram as cd
    proj = parse_project(Path("examples/sample"))
    path = cd(proj, tmp_path)
    assert path and Path(path).stat().st_size > 0
