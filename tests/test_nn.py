"""Тесты нейросетевого модуля (23 сети)."""

from pathlib import Path

from gostdoc.nn import networks, run_all
from gostdoc.nn.net import Net
from gostdoc.parser.cpp_parser import parse_project


def test_23_networks_registered():
    nets = networks()
    assert len(nets) == 23
    assert len({n.name for n in nets}) == 23
    cats = {n.category for n in nets}
    assert len(cats) == 4


def test_net_feed_linear():
    net = Net("t", "cat", "d", weights={"x": 2.0}, bias=1.0)
    assert net.feed({"x": 3.0}) == 7.0


def test_net_feed_sigmoid():
    net = Net("t", "cat", "d", weights={"x": 1.0}, bias=0.0, activation="sigmoid")
    assert 0.5 < net.feed({"x": 5.0}) < 1.0


def test_run_all_on_sample():
    proj = parse_project(Path("examples/sample"))
    results = run_all(proj)
    assert len(results) == 23
    for r in results:
        assert r.net_name and r.text


def test_nn_in_txt(tmp_path):
    from gostdoc.cli import build_docs
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="X", nn=True)
    text = results[0].read_text(encoding="utf-8")
    assert "нейросетевого анализа" in text
    assert "GOSTComplianceChecker" in text
