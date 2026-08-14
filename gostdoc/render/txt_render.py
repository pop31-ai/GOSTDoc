"""Рендер в TXT (моноширинный, с отступами)."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project
from ..styles.docs import get_doc
from .bodies import body_for


def render_txt(proj: Project, out_path: Path, doc_code: str = "19.402") -> Path:
    import datetime

    doc = get_doc(doc_code)
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f"{proj.organisation.upper()}".center(72))
    lines.append("")
    lines.append(f"{proj.name}".center(72))
    lines.append(doc.title.center(72))
    lines.append(doc.subtitle.center(72))
    lines.append("")
    lines.append(f"Разработал: {proj.author or '________'}")
    lines.append(f"Дата: {datetime.date.today().isoformat()}")
    lines.append(f"Документ: ГОСТ {doc.code} (ЕСПД)")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Аннотация")
    lines.append("Документ соответствует требованиям ЕСПД (ГОСТ 19) и ГОСТ 2.105.")
    if proj.comment:
        lines.append(proj.comment)
    lines.append("")
    lines.append("Содержание")
    for num, title, _k in doc.sections:
        lines.append(f"  {num}. {title}")
    lines.append("")
    lines.append("=" * 72)

    for num, title, key in doc.sections:
        lines.append(f"\n{num}. {title}")
        lines.append("-" * 40)
        lines.append(body_for(proj, key))

    lines.append("")
    lines.append("Приложение А. Структура программы")
    lines.append("=" * 72)
    for cls in proj.classes:
        lines.append(f"\nКласс {cls.name}" + (f" : {cls.base}" if cls.base else ""))
        if cls.comment:
            lines.append(f"  // {cls.comment}")
        for f_ in cls.fields:
            lines.append(f"  - поле: {f_}")
        for m in cls.methods:
            kind = {"signal": "сигнал", "slot": "слот"}.get(m.kind, "метод")
            lines.append(f"  - {kind}: {m.return_type} {m.name}({', '.join(m.params)})")
            if m.brief:
                lines.append(f"        описание: {m.brief}")
            for pname, pdesc in m.params_doc.items():
                lines.append(f"        параметр {pname}: {pdesc}")
            if m.returns:
                lines.append(f"        возвращает: {m.returns}")
            for c in m.calls:
                lines.append(f"        -> {c}()")
            for s, r, sig, slot in m.connections:
                lines.append(f"        connect({s}, {sig}() -> {r}, {slot}())")
    for fn in proj.functions:
        lines.append(f"\nФункция {fn.name}  [{fn.file}:{fn.line}]")
        lines.append(f"  {fn.return_type} {fn.name}({', '.join(fn.params)})")
        for c in fn.calls:
            lines.append(f"        -> {c}()")
        for s, r, sig, slot in fn.connections:
            lines.append(f"        connect({s}, {sig}() -> {r}, {slot}())")

    if proj.nn_results:
        lines.append("")
        lines.append("Приложение Б. Результаты нейросетевого анализа (23 сети)")
        lines.append("=" * 72)
        current = None
        for r in proj.nn_results:
            if r.category != current:
                current = r.category
                lines.append(f"\n{current.upper()}")
            lines.append(f"  {r.net_name}  [score={r.score}]")
            lines.append(f"    {r.text}")

    if doc_code == "19.401" and proj.sources:
        lines.append("")
        lines.append("Приложение В. Текст программы")
        lines.append("=" * 72)
        for src in proj.sources:
            lines.append("")
            lines.append(f"Файл: {src}")
            lines.append("-" * 40)
            try:
                code = Path(src).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(code.splitlines(), start=1):
                lines.append(f"{i:>5} | {line}")

    from .bodies import REV_HEADERS, revision_rows
    lines.append("")
    lines.append("Лист регистрации изменений")
    lines.append("=" * 72)
    lines.append(" | ".join(REV_HEADERS))
    lines.append("-" * 72)
    for row in revision_rows():
        lines.append(" | ".join(row))

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
