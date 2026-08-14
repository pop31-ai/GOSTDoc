"""Рендер в Markdown (для GitHub/README): разделы, таблицы, схемы файлами."""

from __future__ import annotations

import datetime
from pathlib import Path

from ..parser.model import Project
from ..styles.docs import get_doc
from .bodies import body_for


def _copy_diagrams(diagrams: dict | None, out_dir: Path) -> dict[str, str]:
    """Копирует схемы в out_dir/figures и возвращает их имена."""
    import shutil
    figs = out_dir / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    for key, path in (diagrams or {}).items():
        if isinstance(path, str):
            name = f"{key}.png"
            try:
                shutil.copy2(path, figs / name)
            except OSError:
                continue
            out[key] = f"figures/{name}"
    flows = (diagrams or {}).get("flows") or {}
    flow_names = {}
    for i, fname in enumerate(sorted(flows)):
        dst = f"figures/flow_{i}.png"
        try:
            shutil.copy2(flows[fname], out_dir / dst)
        except OSError:
            continue
        flow_names[fname] = dst
    seqs = (diagrams or {}).get("seq") or {}
    seq_names = {}
    for i, entry in enumerate(sorted(seqs)):
        dst = f"figures/seq_{i}.png"
        try:
            shutil.copy2(seqs[entry], out_dir / dst)
        except OSError:
            continue
        seq_names[entry] = dst
    out["flows"] = flow_names
    out["seq"] = seq_names
    return out


def render_md(proj: Project, out_path: Path, diagrams: dict | None = None,
              doc_code: str = "19.402") -> Path:
    doc_spec = get_doc(doc_code)
    figs = _copy_diagrams(diagrams, out_path.parent)
    b: list[str] = []

    b.append(f"# {proj.name}")
    b.append("")
    b.append(f"**{doc_spec.title}. {doc_spec.subtitle}**  ")
    b.append(f"Разработал: {proj.author or '________'}  ")
    b.append(f"Дата: {datetime.date.today().isoformat()}  ")
    b.append(f"Документ: ГОСТ {doc_spec.code} (ЕСПД)")
    b.append("")

    b.append("## Аннотация")
    b.append("")
    b.append(f"Документ «{doc_spec.subtitle}» для программы «{proj.name}» "
             f"по ЕСПД (ГОСТ 19), ГОСТ 2.105."
             + (f" {proj.comment}" if proj.comment else ""))
    b.append("")

    b.append("## Содержание")
    b.append("")
    for num, title, _k in doc_spec.sections:
        b.append(f"{num}. [{title}](#sec{num})")
    b.append("")

    for num, title, key in doc_spec.sections:
        b.append(f"<a id=\"sec{num}\"></a>## {num}. {title}")
        b.append("")
        b.append(body_for(proj, key).replace("\n", "  \n"))
        b.append("")

    b.append("## Приложение А. Структура программы")
    b.append("")
    bl = proj.build
    if bl.kind:
        b.append(f"**Система сборки:** {'CMake' if bl.kind == 'cmake' else 'qmake'}"
                 + (f" {bl.version}" if bl.version else "") + "  ")
        if bl.targets:
            b.append(f"**Цели:** {', '.join(bl.targets)}  ")
        if bl.qt_modules:
            b.append(f"**Модули Qt:** {', '.join(bl.qt_modules)}  ")
        if bl.dependencies:
            b.append(f"**Зависимости:** {', '.join(bl.dependencies)}  ")
        b.append("")

    fig = 1
    for img_key, cap in (("classes", "Рисунок А.1 — Диаграмма классов"),
                         ("calls", "Рисунок А.2 — Граф вызовов")):
        if img_key in figs:
            b.append(f"![{cap}]({figs[img_key]})  ")
            b.append(f"*{cap}*")
            b.append("")
            fig += 1
    for fname, dst in figs.get("flows", {}).items():
        b.append(f"![Блок-схема {fname}]({dst})  ")
        b.append(f"*Рисунок А.{fig} — Блок-схема функции {fname}*")
        b.append("")
        fig += 1
    for entry, dst in figs.get("seq", {}).items():
        b.append(f"![Последовательность {entry}]({dst})  ")
        b.append(f"*Рисунок А.{fig} — Диаграмма последовательности (вход: {entry})*")
        b.append("")
        fig += 1

    b.append("### Классы")
    b.append("")
    b.append("| Член | Объявление |")
    b.append("|---|---|")
    for cls in proj.classes:
        b.append(f"| **{cls.name}**{(' : ' + cls.base) if cls.base else ''} | |")
        for f_ in cls.fields:
            b.append(f"| поле | `{f_}` |")
        for m in cls.methods:
            kind = {"signal": "сигнал", "slot": "слот"}.get(m.kind, "метод")
            b.append(f"| {kind} | `{m.return_type} {m.name}({', '.join(m.params)})` |")
    b.append("")

    if proj.functions:
        b.append("### Свободные функции")
        b.append("")
        b.append("| Функция | Сигнатура |")
        b.append("|---|---|")
        for fn in proj.functions:
            b.append(f"| `{fn.name}` | `{fn.return_type} {fn.name}({', '.join(fn.params)})` |")
        b.append("")

    if proj.nn_results:
        b.append("## Приложение Б. Результаты нейросетевого анализа (23 сети)")
        b.append("")
        b.append("| Сеть | Категория | Оценка | Заключение |")
        b.append("|---|---|---|---|")
        for r in proj.nn_results:
            b.append(f"| {r.net_name} | {r.category} | {r.score} | {r.text} |")
        b.append("")

    b.append("## Лист регистрации изменений")
    b.append("")
    from .bodies import REV_HEADERS, revision_rows
    b.append("| " + " | ".join(REV_HEADERS) + " |")
    b.append("|" + "---|" * len(REV_HEADERS))
    for row in revision_rows():
        b.append("| " + " | ".join(row) + " |")

    out_path.write_text("\n".join(b) + "\n", encoding="utf-8")
    return out_path
