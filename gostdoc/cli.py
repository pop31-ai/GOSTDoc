"""CLI: gostdoc --project ./src --out ./docs --format pdf,docx,txt"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from . import __version__
from .grapher.graphs import call_graph, class_diagram, flowcharts
from .parser.cpp_parser import parse_project


def build_docs(project: str, out: str, fmt: tuple[str, ...],
               name: str = "", author: str = "",
               organisation: str = "", comment: str = "",
               nn: bool = False) -> list[Path]:
    src = Path(project)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    proj = parse_project(src, name=name, author=author,
                         organisation=organisation, comment=comment)

    if nn:
        from .nn import run_all, print_report
        proj.nn_results = run_all(proj)
        print_report(proj.nn_results)

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        diagrams = {
            "classes": class_diagram(proj, tdir),
            "calls": call_graph(proj, tdir),
            "flows": flowcharts(proj, tdir),
        }
        results: list[Path] = []
        for f in fmt:
            if f == "docx":
                from .render.docx_render import render_docx
                results.append(render_docx(proj, out_dir / f"{proj.name}.docx", diagrams))
            elif f == "pdf":
                from .render.pdf_render import render_pdf
                results.append(render_pdf(proj, out_dir / f"{proj.name}.pdf", diagrams))
            elif f == "txt":
                from .render.txt_render import render_txt
                results.append(render_txt(proj, out_dir / f"{proj.name}.txt"))
            elif f == "json":
                results.append(_render_json(proj, out_dir / f"{proj.name}.json"))
    return results


def _render_json(proj: Project, out_path: Path) -> Path:
    import json
    from dataclasses import asdict

    data = asdict(proj)
    data["nn_results"] = [
        {"net": r.net_name, "category": r.category, "score": r.score, "text": r.text}
        for r in proj.nn_results
    ]
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gostdoc",
        description="Генератор документации по ГОСТ 19 для программ на C++/Qt.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--project", "-p", default=".", help="каталог с исходниками C++")
    parser.add_argument("--out", "-o", default="./docs", help="каталог для документации")
    parser.add_argument("--format", "-f", default="pdf,docx,txt",
                        help="форматы: pdf,docx,txt,json через запятую")
    parser.add_argument("--name", default="", help="название программы")
    parser.add_argument("--author", default="", help="разработчик")
    parser.add_argument("--organisation", default="", help="организация")
    parser.add_argument("--comment", default="", help="аннотация к программе")
    parser.add_argument("--nn", action="store_true",
                        help="запустить 23 нейросети для анализа и вывод в документ")
    args = parser.parse_args(argv)

    fmt = tuple(x.strip().lower() for x in args.format.split(",") if x.strip())
    try:
        results = build_docs(args.project, args.out, fmt,
                             name=args.name, author=args.author,
                             organisation=args.organisation, comment=args.comment,
                             nn=args.nn)
    except Exception as e:  # noqa: BLE001
        parser.error(f"ошибка: {e}")

    for r in results:
        print(f"сгенерировано: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
