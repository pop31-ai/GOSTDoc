"""CLI: gostdoc --project ./src --out ./docs --format pdf,docx,txt"""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

from . import __version__
from .grapher.graphs import call_graph, class_diagram, flowcharts, sequence_diagrams
from .parser.cpp_parser import parse_project
from .parser.model import Project
from .styles.docs import ALL_CODES

_CONFIG_NAME = ".gostdoc.json"
_KEYS = ("project", "out", "format", "name", "author", "organisation",
         "comment", "nn", "doctype", "zip")


def build_docs(project: str, out: str, fmt: tuple[str, ...],
               name: str = "", author: str = "",
               organisation: str = "", comment: str = "",
               nn: bool = False, doctype: str = "19.402",
               zip_out: bool = False) -> list[Path]:
    src = Path(project)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)

    proj = parse_project(src, name=name, author=author,
                         organisation=organisation, comment=comment)

    if nn:
        from .nn import run_all, print_report
        proj.nn_results = run_all(proj)
        print_report(proj.nn_results)

    if doctype == "all":
        codes = list(ALL_CODES)
    else:
        codes = [doctype]

    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        diagrams = {
            "classes": class_diagram(proj, tdir),
            "calls": call_graph(proj, tdir),
            "flows": flowcharts(proj, tdir),
            "seq": sequence_diagrams(proj, tdir),
        }

        results: list[Path] = []
        for code in codes:
            prefix = f"{code}_" if len(codes) > 1 else ""
            for f in fmt:
                if f == "docx":
                    from .render.docx_render import render_docx
                    results.append(render_docx(proj, out_dir / f"{prefix}{proj.name}.docx", diagrams, code))
                elif f == "pdf":
                    from .render.pdf_render import render_pdf
                    results.append(render_pdf(proj, out_dir / f"{prefix}{proj.name}.pdf", diagrams, code))
                elif f == "txt":
                    from .render.txt_render import render_txt
                    results.append(render_txt(proj, out_dir / f"{prefix}{proj.name}.txt", code))
                elif f == "html":
                    from .render.html_render import render_html
                    results.append(render_html(proj, out_dir / f"{prefix}{proj.name}.html", diagrams, code))
                elif f == "md":
                    from .render.md_render import render_md
                    results.append(render_md(proj, out_dir / f"{prefix}{proj.name}.md", diagrams, code))
                elif f == "json":
                    results.append(_render_json(proj, out_dir / f"{prefix}{proj.name}.json"))

    if zip_out and results:
        zip_path = out_dir / f"{proj.name}_docs.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                zf.write(r, r.name)
        results.append(zip_path)
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


def _write_config_template() -> None:
    cfg_path = Path(_CONFIG_NAME)
    if cfg_path.exists():
        print(f"конфигурация уже существует: {cfg_path}")
        return
    template = {
        "project": "./src",
        "out": "./docs",
        "format": "pdf,docx,txt",
        "name": "",
        "author": "",
        "organisation": "",
        "comment": "",
        "nn": False,
        "doctype": "19.402",
        "zip": False,
    }
    cfg_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"создано: {cfg_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gostdoc",
        description="Генератор документации по ГОСТ 19 для программ на C++/Qt.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--project", "-p", default=".", help="каталог с исходниками C++")
    parser.add_argument("--out", "-o", default="./docs", help="каталог для документации")
    parser.add_argument("--format", "-f", default="pdf,docx,txt",
                        help="форматы: pdf,docx,txt,html,md,json через запятую")
    parser.add_argument("--name", default="", help="название программы")
    parser.add_argument("--author", default="", help="разработчик")
    parser.add_argument("--organisation", default="", help="организация")
    parser.add_argument("--comment", default="", help="аннотация к программе")
    parser.add_argument("--nn", action="store_true",
                        help="запустить 23 нейросети для анализа и вывод в документ")
    parser.add_argument("--doctype", default="19.402",
                        help="тип документа: 19.401, 19.402, 19.403, 19.404, 19.505 или all")
    parser.add_argument("--config", "-c", default="",
                        help="файл конфигурации (.gostdoc.json)")
    parser.add_argument("--zip", action="store_true",
                        help="упаковать все сгенерированные документы в ZIP")
    parser.add_argument("--init", action="store_true",
                        help="создать шаблон конфигурации .gostdoc.json в текущем каталоге")
    parser.add_argument("--check", action="store_true",
                        help="проверить исходники на соответствие ЕСПД (без генерации)")
    args = parser.parse_args(argv)

    if args.init:
        _write_config_template()
        return 0

    if args.check:
        from .check import check_project, print_report
        src = Path(args.project)
        proj = parse_project(src, name=args.name, author=args.author,
                             organisation=args.organisation, comment=args.comment)
        report = check_project(proj)
        print_report(report)
        return 1 if report.errors else 0

    # конфигурация: файл -> аргументы (файл имеет приоритет над дефолтами)
    cfg: dict = {}
    cfg_path = Path(args.config) if args.config else Path(_CONFIG_NAME)
    if cfg_path.exists():
        raw = cfg_path.read_bytes()
        for enc in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                cfg = json.loads(raw.decode(enc))
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
    # приоритет: явные аргументы CLI > конфигурация > дефолты
    dflt = {k: parser.get_default(k) for k in _KEYS}
    resolved: dict = {}
    for k in _KEYS:
        arg_v = getattr(args, k)
        if arg_v != dflt.get(k):
            resolved[k] = arg_v
        else:
            cfg_v = cfg.get(k)
            resolved[k] = cfg_v if cfg_v not in (None, "") else arg_v
    resolved["nn"] = bool(resolved.get("nn"))
    resolved["zip"] = bool(resolved.get("zip"))
    resolved["doctype"] = resolved.get("doctype") or "19.402"
    resolved["format"] = tuple(x.strip().lower() for x in resolved["format"].split(",")
                               if x.strip())
    try:
        results = build_docs(resolved["project"], resolved["out"], resolved["format"],
                             name=resolved["name"], author=resolved["author"],
                             organisation=resolved["organisation"],
                             comment=resolved["comment"], nn=resolved["nn"],
                             doctype=resolved["doctype"], zip_out=resolved["zip"])
    except Exception as e:  # noqa: BLE001
        parser.error(f"ошибка: {e}")

    for r in results:
        print(f"сгенерировано: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
