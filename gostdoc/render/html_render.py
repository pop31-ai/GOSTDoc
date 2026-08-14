"""Рендер в HTML (один файл, схемы встраиваются как base64)."""

from __future__ import annotations

import base64
import html
from pathlib import Path

from ..parser.model import Project
from ..styles.docs import get_doc
from .bodies import body_for


def _img_b64(path: str | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_html(proj: Project, out_path: Path, diagrams: dict | None = None,
                doc_code: str = "19.402") -> Path:
    import datetime

    doc_spec = get_doc(doc_code)
    b = []  # тело

    b.append(f'<h1>{_esc(proj.organisation.upper())}</h1>')
    b.append(f'<h2>{_esc(proj.name)}</h2>')
    b.append(f'<p class="center"><b>{_esc(doc_spec.title)}</b><br>{_esc(doc_spec.subtitle)}</p>')
    b.append(f'<p>Разработал: {_esc(proj.author or "________")}<br>'
             f'Дата: {datetime.date.today().isoformat()}<br>'
             f'Документ: ГОСТ {doc_spec.code} (ЕСПД)</p>')

    b.append('<hr>')
    b.append('<h3>Аннотация</h3>')
    b.append(f'<p>Документ «{_esc(doc_spec.subtitle)}» для программы «{_esc(proj.name)}» '
             f'по ЕСПД (ГОСТ 19), ГОСТ 2.105.{(" " + _esc(proj.comment)) if proj.comment else ""}</p>')

    b.append('<h3>Содержание</h3><ol>')
    for num, title, _k in doc_spec.sections:
        b.append(f'<li><a href="#sec{num}">{num}. {_esc(title)}</a></li>')
    b.append('</ol>')

    for num, title, key in doc_spec.sections:
        b.append(f'<h3 id="sec{num}">{num}. {_esc(title)}</h3>')
        b.append(f'<p>{_esc(body_for(proj, key))}</p>')

    b.append('<h3>Приложение А. Структура программы</h3>')
    fig = 1
    bl = proj.build
    if bl.kind:
        b.append(f'<p><b>Система сборки:</b> {"CMake" if bl.kind == "cmake" else "qmake"}'
                 + (f' {_esc(bl.version)}' if bl.version else '') + '</p>')
        if bl.targets:
            b.append(f'<p><b>Цели:</b> {_esc(", ".join(bl.targets))}</p>')
        if bl.qt_modules:
            b.append(f'<p><b>Модули Qt:</b> {_esc(", ".join(bl.qt_modules))}</p>')
        if bl.dependencies:
            b.append(f'<p><b>Зависимости:</b> {_esc(", ".join(bl.dependencies))}</p>')
    for img_key, cap in (("classes", "Рисунок А.1 — Диаграмма классов"),
                         ("calls", "Рисунок А.2 — Граф вызовов")):
        data = _img_b64(diagrams.get(img_key)) if diagrams else None
        if data:
            b.append(f'<img src="data:image/png;base64,{data}" alt="{cap}"><p class="fig">{cap}</p>')
            fig += 1
    flows = (diagrams or {}).get("flows") or {}
    for fname in sorted(flows):
        data = _img_b64(flows[fname])
        if data:
            cap = f'Рисунок А.{fig} — Блок-схема функции {_esc(fname)}'
            b.append(f'<img src="data:image/png;base64,{data}" alt="{cap}"><p class="fig">{cap}</p>')
            fig += 1
    seqs = (diagrams or {}).get("seq") or {}
    for entry in sorted(seqs):
        data = _img_b64(seqs[entry])
        if data:
            cap = f'Рисунок А.{fig} — Диаграмма последовательности (вход: {_esc(entry)})'
            b.append(f'<img src="data:image/png;base64,{data}" alt="{cap}"><p class="fig">{cap}</p>')
            fig += 1

    b.append('<h4>Классы</h4><table border="1" cellspacing="0" cellpadding="4">')
    for cls in proj.classes:
        head = f'{_esc(cls.name)}' + (f' : {_esc(cls.base)}' if cls.base else '')
        b.append(f'<tr><th colspan="2">{head}</th></tr>')
        for f_ in cls.fields:
            b.append(f'<tr><td>поле</td><td>{_esc(f_)}</td></tr>')
        for m in cls.methods:
            row = f'<tr><td>{_esc({"signal": "сигнал", "slot": "слот"}.get(m.kind, "метод"))}</td>' \
                  f'<td>{_esc(m.return_type)} {_esc(m.name)}' \
                  f'({_esc(", ".join(m.params))})</td></tr>'
            b.append(row)
            if m.brief:
                b.append(f'<tr><td></td><td><i>{_esc(m.brief)}</i></td></tr>')
    b.append('</table>')

    if proj.functions:
        b.append('<h4>Свободные функции</h4><ul>')
        for fn in proj.functions:
            b.append(f'<li><b>{_esc(fn.name)}</b> — {_esc(fn.return_type)} '
                     f'({_esc(", ".join(fn.params))}), файл {_esc(fn.file)}:{fn.line}</li>')
        b.append('</ul>')

    if proj.nn_results:
        b.append('<h3>Приложение Б. Результаты нейросетевого анализа (23 сети)</h3>')
        b.append('<table border="1" cellspacing="0" cellpadding="4">')
        b.append('<tr><th>Сеть</th><th>Категория</th><th>Оценка</th><th>Заключение</th></tr>')
        for r in proj.nn_results:
            b.append(f'<tr><td>{_esc(r.net_name)}</td><td>{_esc(r.category)}</td>'
                     f'<td>{r.score}</td><td>{_esc(r.text)}</td></tr>')
        b.append('</table>')

    if doc_code == "19.401" and proj.sources:
        b.append('<h3>Приложение В. Текст программы</h3>')
        for src in proj.sources:
            b.append(f'<h4>Файл: {_esc(src)}</h4><pre>')
            try:
                code = Path(src).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                code = ""
            for i, line in enumerate(code.splitlines(), start=1):
                b.append(f'{i:>5} | {_esc(line)}')
            b.append('</pre>')

    from .bodies import REV_HEADERS, revision_rows
    b.append('<h3>Лист регистрации изменений</h3>')
    b.append('<table border="1" cellspacing="0" cellpadding="4">')
    b.append('<tr>' + "".join(f'<th>{_esc(h)}</th>' for h in REV_HEADERS) + '</tr>')
    for row in revision_rows():
        b.append('<tr>' + "".join(f'<td>{_esc(v)}</td>' for v in row) + '</tr>')
    b.append('</table>')

    css = """
    body { font-family: "Times New Roman", serif; font-size: 14px;
           line-height: 1.5; margin: 30px 80px 40px 200px;
           text-indent: 1.25cm; }
    h1, h2, h3, h4 { text-indent: 0; text-align: center; }
    h3 { text-align: left; margin-top: 2em; }
    p.center, p.fig { text-align: center; text-indent: 0; }
    table { width: 100%; border-collapse: collapse; text-indent: 0; }
    pre { font-family: "Courier New", monospace; font-size: 10px;
          line-height: 1.2; text-indent: 0; background: #f6f6f6; padding: 8px; }
    li { text-indent: 0; }
    """
    html_doc = f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>{_esc(proj.name)} — {_esc(doc_spec.subtitle)}</title>
<style>{css}</style></head>
<body>
{chr(10).join(b)}
</body></html>"""

    out_path.write_text(html_doc, encoding="utf-8")
    return out_path
