"""Константы оформления по ГОСТ 2.105 / 7.32.

Шрифт: Times New Roman 14 пт, межстрочный интервал 1.5,
поля: левое 30 мм, правое 10 мм, верхнее/нижнее 20 мм,
абзацный отступ 1.25 см.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GOSTStyles:
    font_ru: str = "Times New Roman"
    font_size: int = 14
    line_spacing: float = 1.5
    margin_left_mm: float = 30.0
    margin_right_mm: float = 10.0
    margin_top_mm: float = 20.0
    margin_bottom_mm: float = 20.0
    first_line_indent_cm: float = 1.25
    heading1: str = "1"
    heading2: str = "1.1"
    heading3: str = "1.1.1"

    @property
    def page_width_mm(self) -> float:
        return 210.0  # A4

    @property
    def page_height_mm(self) -> float:
        return 297.0


STYLE = GOSTStyles()

GOST19_402_SECTIONS = [
    ("Назначение и область применения", "opurpose"),
    ("Технические характеристики", "tech"),
    ("Описание программы", "desc"),
    ("Логическая структура", "logic"),
    ("Используемые технические средства", "hardware"),
    ("Вызов и загрузка", "call"),
    ("Входные данные", "input"),
    ("Выходные данные", "output"),
]
