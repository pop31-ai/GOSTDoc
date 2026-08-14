"""Рендер в DOCX (python-docx) по ГОСТ 2.105."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project
from ..styles.gost_styles import STYLE, GOST19_402_SECTIONS


def _section_num(i: int) -> str:
    return f"{i}"


def render_docx(proj: Project, out_path: Path, diagrams: dict | None = None) -> Path:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.shared import Mm, Pt, Cm

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = Mm(STYLE.margin_left_mm)
    sec.right_margin = Mm(STYLE.margin_right_mm)
    sec.top_margin = Mm(STYLE.margin_top_mm)
    sec.bottom_margin = Mm(STYLE.margin_bottom_mm)

    style = doc.styles["Normal"]
    style.font.name = STYLE.font_ru
    style.font.size = Pt(STYLE.font_size)
    style.paragraph_format.line_spacing = STYLE.line_spacing
    style.paragraph_format.first_line_indent = Cm(STYLE.first_line_indent_cm)

    # --- титульный лист ---
    for _ in range(4):
        doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(proj.organisation.upper()).bold = True
    for _ in range(4):
        doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(proj.name)
    r.font.size = Pt(18)
    r.bold = True
    doc.add_paragraph("ПРОГРАММА")
    doc.add_paragraph("Руководство программиста. Описание программы")
    for _ in range(5):
        doc.add_paragraph("")
    doc.add_paragraph(f"Разработал: {proj.author or '________'}")
    doc.add_paragraph(f"Дата: {__import__('datetime').date.today().isoformat()}")
    doc.add_page_break()

    # --- аннотация ---
    h = doc.add_paragraph()
    h.add_run("Аннотация").bold = True
    doc.add_paragraph(
        f"Настоящий документ содержит описание программы «{proj.name}» "
        f"и соответствует требованиям ГОСТ 19.402, ГОСТ 2.105. "
        f"{proj.comment}".strip())

    # --- содержание (краткое) ---
    h = doc.add_paragraph()
    h.add_run("Содержание").bold = True
    for num, (title, _key) in enumerate(GOST19_402_SECTIONS, start=1):
        doc.add_paragraph(f"{num}. {title}")

    # --- разделы ---
    for num, (title, key) in enumerate(GOST19_402_SECTIONS, start=1):
        h = doc.add_paragraph()
        h.add_run(f"{num}. {title}").bold = True
        doc.add_paragraph(_body_for(proj, key, diagrams))

    doc.add_page_break()

    # --- приложение: структура кода ---
    h = doc.add_paragraph()
    h.add_run("Приложение А. Структура программы").bold = True

    if diagrams and diagrams.get("classes"):
        doc.add_picture(str(diagrams["classes"]), width=Cm(16))
        doc.add_paragraph("Рисунок А.1 — Диаграмма классов")
    if diagrams and diagrams.get("calls"):
        doc.add_picture(str(diagrams["calls"]), width=Cm(16))
        doc.add_paragraph("Рисунок А.2 — Граф вызовов")

    for cls in proj.classes:
        doc.add_paragraph(f"Класс {cls.name}" + (f" : {cls.base}" if cls.base else "")).bold = True
        if cls.comment:
            doc.add_paragraph(cls.comment)
        if cls.fields:
            doc.add_paragraph("Поля:")
            for f_ in cls.fields:
                doc.add_paragraph(f_ + " —", style="List Bullet")
        if cls.methods:
            doc.add_paragraph("Методы:")
            for m in cls.methods:
                doc.add_paragraph(
                    f"{m.return_type} {m.name}({', '.join(m.params)})",
                    style="List Bullet")

    for fn in proj.functions:
        doc.add_paragraph(f"Функция {fn.name}").bold = True
        doc.add_paragraph(f"{fn.return_type} {fn.name}({', '.join(fn.params)}) — файл {fn.file}:{fn.line}")

    doc.save(str(out_path))
    return out_path


def _body_for(proj: Project, key: str, diagrams: dict | None) -> str:
    if key == "opurpose":
        return f"Программа «{proj.name}» предназначена для обработки данных согласно техническому заданию."
    if key == "desc":
        parts = [f"Программа содержит {len(proj.classes)} классов и {len(proj.functions)} свободных функций."]
        for cls in proj.classes:
            parts.append(f"Класс {cls.name} — {len(cls.methods)} методов, {len(cls.fields)} полей.")
        return " ".join(parts)
    if key == "logic":
        return "Логическая структура отражена на схемах в приложении А."
    if key == "call":
        return "Запуск программы осуществляется из командной строки или среды разработки."
    if key == "input":
        return "Входные данные: исходные файлы проекта, параметры командной строки."
    if key == "output":
        return "Выходные данные: документация в форматах PDF, DOCX, TXT."
    if key == "tech":
        return "Требования: C++/Qt, ОС Windows/Linux."
    return ""
