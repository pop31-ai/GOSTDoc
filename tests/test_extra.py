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
    assert codes == {"19.401", "19.402", "19.403", "19.404", "19.505"}


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
