"""Дополнительные тесты: конструкторы, перегрузки, шаблоны, CLI."""

from pathlib import Path

from gostdoc.cli import build_docs
from gostdoc.parser.cpp_parser import parse_file, parse_project

SRC = """
// Базовый класс.
class Base {
public:
    Base();
    virtual ~Base();
};

// Производный класс.
class Derived : public Base {
public:
    Derived(int x);
    double calc(const double a, const double b) const;
    void notify();
private:
    int value;
    std::string label;
};
"""


def test_ctors_and_dtors(tmp_path: Path):
    f = tmp_path / "a.h"
    f.write_text(SRC, encoding="utf-8")
    classes, _en, _td, _ns = parse_file(f)
    by_name = {c.name: c for c in classes}
    assert "Base" in by_name and "Derived" in by_name
    base = by_name["Base"]
    assert {m.name for m in base.methods} == {"Base", "~Base"}
    derived = by_name["Derived"]
    names = {m.name for m in derived.methods}
    assert "Derived" in names and "calc" in names and "notify" in names


def test_inheritance_base(tmp_path: Path):
    f = tmp_path / "a.h"
    f.write_text(SRC, encoding="utf-8")
    classes, _en, _td, _ns = parse_file(f)
    derived = next(c for c in classes if c.name == "Derived")
    assert derived.base == "Base"


def test_template_method(tmp_path: Path):
    f = tmp_path / "t.h"
    f.write_text("template<class T>\nclass Stack {\npublic:\n    void push(const T& item);\n};",
                 encoding="utf-8")
    classes, _en, _td, _ns = parse_file(f)
    assert classes[0].name == "Stack"
    assert classes[0].methods[0].name == "push"


def test_build_docs_all_formats(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt", "docx", "pdf"), name="Test", author="A")
    files = {r.suffix for r in results}
    assert files == {".txt", ".docx", ".pdf"}
    for r in results:
        assert r.exists() and r.stat().st_size > 0


def test_build_docs_json(tmp_path: Path):
    import json
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("json",), name="J")
    data = json.loads(results[0].read_text(encoding="utf-8"))
    assert data["name"] == "J"
    assert len(data["classes"]) >= 1


def test_conditions_extracted():
    from gostdoc.parser.cpp_parser import _extract_conditions
    src = "if (x > 0) {} while (y) {} for (int i = 0; i < n; i++) {}"
    conds = _extract_conditions(src)
    assert any("if x > 0" in c for c in conds)
    assert any("while y" in c for c in conds)
    assert any("for" in c for c in conds)


def test_doctype_single(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="D", doctype="19.404")
    assert len(results) == 1
    assert "Пояснительная записка" in results[0].read_text(encoding="utf-8")


def test_doctype_all(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="D", doctype="all")
    codes = {p.stem.split("_")[0] for p in results}
    assert codes == {"19.401", "19.402", "19.403", "19.404", "19.504", "19.505"}


def test_docs_all_codes_render_pdf(tmp_path: Path):
    from gostdoc.render.pdf_render import render_pdf
    from gostdoc.styles.docs import ALL_CODES
    from gostdoc.parser.cpp_parser import parse_project
    proj = parse_project(Path("examples/sample"))
    for code in ALL_CODES:
        out = render_pdf(proj, tmp_path / f"{code}.pdf", doc_code=code)
        assert out.exists() and out.stat().st_size > 0


SRC2 = """
namespace app {
enum class Status { OK, ERROR, UNKNOWN };
typedef unsigned int uint_t;
using Flag = int;
class Vec {
public:
    Vec& operator+=(const Vec& o);
    bool operator==(const Vec& o) const;
};
}
"""


def test_parse_enums_typedefs_operators(tmp_path: Path):
    from gostdoc.parser.cpp_parser import parse_file
    f = tmp_path / "b.h"
    f.write_text(SRC2, encoding="utf-8")
    classes, enums, typedefs, namespaces = parse_file(f)
    assert namespaces == ["app"]
    assert enums[0].name == "Status"
    assert enums[0].values[0] == "Status" or "OK" in " ".join(enums[0].values)
    assert len(typedefs) == 2
    names = {m.name for c in classes for m in c.methods}
    assert "operator+=" in names and "operator==" in names


def test_render_html(tmp_path: Path):
    from gostdoc.render.html_render import render_html
    from gostdoc.parser.cpp_parser import parse_project
    proj = parse_project(Path("examples/sample"))
    out = render_html(proj, tmp_path / "doc.html")
    text = out.read_text(encoding="utf-8")
    assert "<html" in text and "Аннотация" in text and "Приложение" in text


def test_build_docs_html(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "o"),
                         ("html",), name="H")
    assert results[0].suffix == ".html"


QT_SRC = """
class Widget : public QWidget {
    Q_OBJECT
public:
    Widget();
    void start();
signals:
    void finished(int code);
public slots:
    void handleDone(int code);
};
"""


def test_qt_signals_slots(tmp_path: Path):
    f = tmp_path / "w.h"
    f.write_text(QT_SRC, encoding="utf-8")
    classes, _en, _td, _ns = parse_file(f)
    w = classes[0]
    kinds = {m.name: m.kind for m in w.methods}
    assert kinds.get("finished") == "signal"
    assert kinds.get("handleDone") == "slot"
    assert kinds.get("start") == "method"


def test_connect_extraction(tmp_path: Path):
    f = tmp_path / "w.cpp"
    f.write_text(
        "void Widget::start() {\n"
        "    connect(btn, &QPushButton::clicked, this, &Widget::handleDone);\n"
        "    connect(this, SIGNAL(finished(int)), app, SLOT(quit()));\n"
        "}", encoding="utf-8")
    from gostdoc.parser.cpp_parser import _extract_connections
    conns = _extract_connections(f.read_text(encoding="utf-8"))
    pairs = {(s, r, sig, slot) for s, r, sig, slot in conns}
    assert ("btn", "this", "clicked", "handleDone") in pairs
    assert ("this", "app", "finished", "quit") in pairs


def test_sequence_diagram(tmp_path: Path):
    from gostdoc.grapher.graphs import sequence_diagrams
    from gostdoc.parser.cpp_parser import parse_project
    proj = parse_project(Path("examples/sample"))
    seqs = sequence_diagrams(proj, tmp_path)
    assert "main" in seqs
    p = Path(seqs["main"])
    assert p.exists() and p.stat().st_size > 0


def test_build_docs_zip(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="Z", zip_out=True)
    zip_path = next(r for r in results if r.suffix == ".zip")
    assert zip_path.exists()
    import zipfile
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert any(n.endswith(".txt") for n in names)


DOXY_SRC = """
// Класс обработки изображений.
class Img {
public:
    /** Выполняет бинаризацию изображения.
     *  @param[in] src исходное изображение
     *  @param threshold порог яркости
     *  @return результат в градациях чёрного и белого
     */
    QImage binarize(const QImage& src, int threshold);
};
"""


def test_doxygen_comments(tmp_path: Path):
    f = tmp_path / "d.h"
    f.write_text(DOXY_SRC, encoding="utf-8")
    classes, _en, _td, _ns = parse_file(f)
    m = next(m for m in classes[0].methods if m.name == "binarize")
    assert "бинаризацию" in m.brief
    assert "src" in m.params_doc and "порог" in m.params_doc["threshold"]
    assert "градациях" in m.returns


def test_doc_19504(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="P", doctype="19.504")
    text = results[0].read_text(encoding="utf-8")
    assert "Руководство программиста" in text
    assert "Структура программы" in text


def test_revision_register(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt", "docx", "pdf"), name="R")
    txt = results[0].read_text(encoding="utf-8")
    assert "Лист регистрации изменений" in txt
    assert "Номер изм." in txt


CMAKE = """
cmake_minimum_required(VERSION 3.16)
project(MyApp VERSION 2.1.0 LANGUAGES CXX)
find_package(Qt6 REQUIRED COMPONENTS Widgets Network)
qt_add_executable(MyApp main.cpp)
target_link_libraries(MyApp PRIVATE Qt6::Widgets)
"""


def test_parse_cmake(tmp_path: Path):
    (tmp_path / "CMakeLists.txt").write_text(CMAKE, encoding="utf-8")
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    from gostdoc.parser.cpp_parser import parse_project
    proj = parse_project(tmp_path)
    assert proj.build.kind == "cmake"
    assert proj.build.name == "MyApp"
    assert proj.build.version == "2.1.0"
    assert proj.build.targets == ["MyApp"]
    assert proj.build.qt_modules == ["Widgets", "Network"]


def test_parse_pro(tmp_path: Path):
    (tmp_path / "app.pro").write_text(
        "TARGET = MyApp\nQT += core gui widgets\n", encoding="utf-8")
    from gostdoc.parser.build_parser import parse_build
    info = parse_build(tmp_path)
    assert info.kind == "qmake"
    assert info.name == "MyApp"
    assert info.qt_modules == ["core", "gui", "widgets"] or \
        {"core", "gui", "widgets"} <= set(info.qt_modules)


def test_sample_uses_cmake():
    from gostdoc.parser.cpp_parser import parse_project
    proj = parse_project(Path("examples/sample"))
    assert proj.build.kind == "cmake"
    assert proj.build.name == "SampleApp"
    assert "Widgets" in proj.build.qt_modules


def test_glossary_19_404(tmp_path: Path):
    results = build_docs(str(Path("examples/sample")), str(tmp_path / "out"),
                         ("txt",), name="G", doctype="19.404")
    text = results[0].read_text(encoding="utf-8")
    assert "Термины и сокращения" in text
    assert "MainWindow" in text
