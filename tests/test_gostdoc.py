"""Тесты парсера и рендеров."""

from pathlib import Path

from gostdoc.parser.cpp_parser import parse_file, parse_project

SAMPLE = """
// Класс кофеварки.
class CoffeeMachine {
public:
    CoffeeMachine();
    void brew(const QString& type);
    int cups;
private:
    int temperature;
    bool on;
};
"""


def test_parse_class():
    path = Path("examples/sample/mainwindow.h")
    assert path.exists(), "пример отсутствует"
    classes, _en, _td, _ns = parse_file(path)
    names = [c.name for c in classes]
    assert "MainWindow" in names
    assert "ImageProcessor" in names


def test_parse_class_fields_methods():
    tmp = Path("examples/sample/_tmp.h")
    tmp.write_text(SAMPLE, encoding="utf-8")
    try:
        classes, _en, _td, _ns = parse_file(tmp)
        cm = classes[0]
        assert cm.name == "CoffeeMachine"
        assert {m.name for m in cm.methods} == {"CoffeeMachine", "brew"}
        assert "int cups" in cm.fields
    finally:
        tmp.unlink()


def test_parse_project_calls():
    proj = parse_project(Path("examples/sample"))
    names = {f.name for f in proj.all_functions()}
    assert "MainWindow" in names
    assert "openFile" in names
    assert ("processImage", "grayscale") in proj.call_edges or \
           any(src == "processImage" for src, _ in proj.call_edges)


def test_render_txt():
    from gostdoc.render.txt_render import render_txt
    proj = parse_project(Path("examples/sample"))
    out = Path("docs/test.txt")
    out.parent.mkdir(exist_ok=True)
    render_txt(proj, out)
    text = out.read_text(encoding="utf-8")
    assert "ПРОГРАММА" in text
    assert "CoffeeMachine" in text or "MainWindow" in text
    out.unlink()
