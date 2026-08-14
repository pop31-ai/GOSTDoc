"""Рендер в TXT (моноширинный, с отступами)."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project
from ..styles.gost_styles import GOST19_402_SECTIONS


def render_txt(proj: Project, out_path: Path) -> Path:
    import datetime

    lines: list[str] = []
    lines.append("=" * 72)
    lines.append(f"{proj.organisation.upper()}".center(72))
    lines.append("")
    lines.append(f"{proj.name}".center(72))
    lines.append("ПРОГРАММА".center(72))
    lines.append("Руководство программиста. Описание программы".center(72))
    lines.append("")
    lines.append(f"Разработал: {proj.author or '________'}")
    lines.append(f"Дата: {datetime.date.today().isoformat()}")
    lines.append("=" * 72)
    lines.append("")
    lines.append("Аннотация")
    lines.append("Документ соответствует ГОСТ 19.402, ГОСТ 2.105.")
    if proj.comment:
        lines.append(proj.comment)
    lines.append("")
    lines.append("Содержание")
    for num, (title, _k) in enumerate(GOST19_402_SECTIONS, start=1):
        lines.append(f"  {num}. {title}")
    lines.append("")
    lines.append("=" * 72)

    for num, (title, _k) in enumerate(GOST19_402_SECTIONS, start=1):
        lines.append(f"\n{num}. {title}")
        lines.append("-" * 40)
        lines.append(_body_for(proj, num))

    lines.append("Приложение А. Структура программы")
    lines.append("=" * 72)
    for cls in proj.classes:
        lines.append(f"\nКласс {cls.name}" + (f" : {cls.base}" if cls.base else ""))
        if cls.comment:
            lines.append(f"  // {cls.comment}")
        for f_ in cls.fields:
            lines.append(f"  - поле: {f_}")
        for m in cls.methods:
            lines.append(f"  - метод: {m.return_type} {m.name}({', '.join(m.params)})")
            for c in m.calls:
                lines.append(f"        -> {c}()")
    for fn in proj.functions:
        lines.append(f"\nФункция {fn.name}  [{fn.file}:{fn.line}]")
        lines.append(f"  {fn.return_type} {fn.name}({', '.join(fn.params)})")
        for c in fn.calls:
            lines.append(f"        -> {c}()")

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

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def _body_for(proj: Project, num: int) -> str:
    if num == 1:
        return f"Программа «{proj.name}» предназначена для обработки данных согласно техническому заданию."
    if num == 2:
        return "Требования: C++/Qt, ОС Windows/Linux."
    if num == 3:
        parts = [f"Программа содержит {len(proj.classes)} классов и {len(proj.functions)} свободных функций."]
        for cls in proj.classes:
            parts.append(f"Класс {cls.name} — {len(cls.methods)} методов, {len(cls.fields)} полей.")
        return " ".join(parts)
    if num == 4:
        return "Логическая структура отражена на схемах (см. сгенерированные PNG-файлы)."
    if num == 5:
        return "Используемые технические средства: ПЭВМ, ОС Windows/Linux."
    if num == 6:
        return "Запуск программы осуществляется из командной строки или среды разработки."
    if num == 7:
        return "Входные данные: исходные файлы проекта, параметры командной строки."
    return "Выходные данные: документация в форматах PDF, DOCX, TXT."
