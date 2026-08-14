"""Рендер в PDF (fpdf2). Кириллический шрифт берётся из системных TTF."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project
from ..styles.gost_styles import STYLE, GOST19_402_SECTIONS

_WINDOWS_FONTS = [
    Path("C:/Windows/Fonts/times.ttf"),        # Times New Roman
    Path("C:/Windows/Fonts/timesbd.ttf"),
    Path("C:/Windows/Fonts/timesi.ttf"),
]
_LINUX_FONTS = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
]


def _find_font() -> Path | None:
    for p in _WINDOWS_FONTS + _LINUX_FONTS:
        if p.exists():
            return p
    return None


def render_pdf(proj: Project, out_path: Path, diagrams: dict | None = None) -> Path:
    from fpdf import FPDF

    font = _find_font()
    if font is None:
        raise RuntimeError("Кириллический TTF-шрифт не найден; установите Times New Roman или DejaVu.")

    pdf = FPDF(unit="mm", format="A4")
    pdf.set_margins(STYLE.margin_left_mm, STYLE.margin_top_mm, STYLE.margin_right_mm)
    pdf.set_auto_page_break(auto=True, margin=STYLE.margin_bottom_mm)
    pdf.add_font("GOST", "", str(font))
    pdf.add_font("GOST", "B", str(font))
    pdf.add_page()

    lh = STYLE.font_size * 0.5  # высота строки ~14pt*1.5/2

    def para(text: str, size: int = STYLE.font_size, bold: bool = False, center: bool = False):
        pdf.set_font("GOST", "B" if bold else "", size)
        pdf.multi_cell(0, lh, text, align="C" if center else "L", new_x="LMARGIN", new_y="NEXT")

    def spacing(n=1):
        for _ in range(n):
            pdf.ln(lh / 2)

    # титульный лист
    spacing(5)
    para(proj.organisation.upper(), 16, center=True)
    spacing(4)
    para(proj.name, 18, bold=True, center=True)
    para("ПРОГРАММА", 14, center=True)
    para("Руководство программиста. Описание программы", 14, center=True)
    spacing(5)
    para(f"Разработал: {proj.author or '________'}")
    para(f"Дата: {__import__('datetime').date.today().isoformat()}")
    pdf.add_page()

    para("Аннотация", bold=True)
    para(f"Документ содержит описание программы «{proj.name}» "
         f"по ГОСТ 19.402, ГОСТ 2.105. {proj.comment}".strip())
    spacing()
    para("Содержание", bold=True)
    for num, (title, _k) in enumerate(GOST19_402_SECTIONS, start=1):
        para(f"{num}. {title}")

    for num, (title, key) in enumerate(GOST19_402_SECTIONS, start=1):
        pdf.add_page()
        para(f"{num}. {title}", bold=True)
        para(_body_for(proj, key))

    pdf.add_page()
    para("Приложение А. Структура программы", bold=True)
    for img_key, cap in (("classes", "Рисунок А.1 — Диаграмма классов"),
                         ("calls", "Рисунок А.2 — Граф вызовов")):
        if diagrams and diagrams.get(img_key):
            img = diagrams[img_key]
            w = pdf.w - STYLE.margin_left_mm - STYLE.margin_right_mm - 10
            try:
                pdf.image(str(img), w=w)
            except Exception:
                continue
            pdf.ln(2)
            para(cap)
            pdf.add_page()
    for cls in proj.classes:
        para(f"Класс {cls.name}" + (f" : {cls.base}" if cls.base else ""), bold=True)
        if cls.comment:
            para(cls.comment)
        for f_ in cls.fields:
            para(f"— {f_}")
        for m in cls.methods:
            para(f"— {m.return_type} {m.name}({', '.join(m.params)})")

    if proj.nn_results:
        pdf.add_page()
        para("Приложение Б. Результаты нейросетевого анализа (23 сети)", bold=True)
        current = None
        for r in proj.nn_results:
            if r.category != current:
                current = r.category
                para(r.category.upper(), bold=True)
            para(f"{r.net_name} [score={r.score}]", bold=True)
            para(r.text)

    pdf.output(str(out_path))
    return out_path


def _body_for(proj: Project, key: str) -> str:
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
