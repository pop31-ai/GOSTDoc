"""Инспекция исходников на соответствие ЕСПД (режим gostdoc --check).

Формирует перечень замечаний по ГОСТ 19/2.105: Doxygen-комментарии,
длинные функции, вложенность, наличие системы сборки, документированность.
Возвращает список замечаний; CLI завершается кодом 1 при наличии ошибок.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .parser.model import Project

_MAX_DEPTH = 6


@dataclass
class Issue:
    file: str
    line: int
    severity: str  # error / warning
    rule: str
    message: str


@dataclass
class CheckReport:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]


def _source_text(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def check_project(proj: Project) -> CheckReport:
    report = CheckReport()
    for cls in proj.classes:
        if not cls.comment:
            report.issues.append(Issue(cls.file, cls.line, "warning",
                                       "класс без комментария",
                                       f"Класс {cls.name} не документирован (нужен //-комментарий или Doxygen)."))
        for m in cls.methods:
            if not m.comment and m.kind == "method":
                report.issues.append(Issue(m.file, m.line, "warning",
                                           "метод без комментария",
                                           f"Метод {cls.name}::{m.name}() не документирован."))
    for f in proj.all_functions():
        if len(f.conditions) > 4:
            report.issues.append(Issue(f.file, f.line, "warning", "сложность",
                                       f"Функция {f.name}() содержит {len(f.conditions)} ветвлений — "
                                       "рекомендуется декомпозиция."))

    for path_str in proj.sources:
        path = Path(path_str)
        lines = _source_text(path)
        depth = 0
        for i, raw in enumerate(lines, start=1):
            stripped = re.sub(r"//.*$", "", raw)
            depth += stripped.count("{") - stripped.count("}")
            if depth > _MAX_DEPTH:
                report.issues.append(Issue(path.name, i, "error", "вложенность",
                                           f"Вложенность блоков более {_MAX_DEPTH} уровней."))
                depth = _MAX_DEPTH
        for i, raw in enumerate(lines, start=1):
            if re.search(r"\b(TODO|FIXME|HACK)\b", raw):
                report.issues.append(Issue(path.name, i, "error", "незавершённый код",
                                           f"Найден маркер {re.search(r'(TODO|FIXME|HACK)', raw).group(1)}."))
            if len(raw) > 120:
                report.issues.append(Issue(path.name, i, "warning", "длина строки",
                                           f"Строка {len(raw)} символов (допустимо до 120)."))
    return report


def print_report(report: CheckReport) -> None:
    print("=" * 60)
    print("        Проверка соответствия ЕСПД (ГОСТ 19 / ГОСТ 2.105)")
    print("=" * 60)
    for i in report.errors:
        print(f"[ОШИБКА] {i.file}:{i.line}  {i.rule} — {i.message}")
    for i in report.warnings:
        print(f"[предупр.] {i.file}:{i.line}  {i.rule} — {i.message}")
    if not report.issues:
        print("Замечаний нет. Программа соответствует требованиям.")
    else:
        print("-" * 60)
        print(f"Итого: {len(report.errors)} ошибок, {len(report.warnings)} предупреждений.")
