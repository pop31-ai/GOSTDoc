"""Единый генератор текста разделов для всех документов и форматов."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project


def body_for(proj: Project, key: str) -> str:
    funcs = proj.all_functions()
    n_methods = sum(1 for f in funcs if f.is_method)
    n_lines = sum(1 for s in proj.sources for _ in
                  Path(s).read_text(encoding="utf-8", errors="ignore").splitlines())
    if key == "purpose":
        return f"Программа «{proj.name}» предназначена для обработки данных согласно техническому заданию."
    if key == "tech":
        parts = ["Требования к техническим средствам: ПЭВМ, ОС Windows/Linux, среда выполнения C++/Qt."]
        b = proj.build
        if b.kind:
            parts.append(f"Система сборки: {'CMake' if b.kind == 'cmake' else 'qmake'}"
                         + (f" (версия {b.version})" if b.version else "") + ".")
        if b.targets:
            parts.append("Цели сборки: " + ", ".join(b.targets) + ".")
        if b.qt_modules:
            parts.append("Модули Qt: " + ", ".join(b.qt_modules) + ".")
        if b.dependencies:
            parts.append("Внешние зависимости: " + ", ".join(b.dependencies) + ".")
        return " ".join(parts)
    if key == "description":
        parts = [f"Программа содержит {len(proj.classes)} классов и {len(proj.functions)} свободных функций."]
        for cls in proj.classes:
            parts.append(f"Класс {cls.name} — {len(cls.methods)} методов, {len(cls.fields)} полей.")
        return " ".join(parts)
    if key == "logic":
        return "Логическая структура отражена на схемах в приложении (диаграммы классов, граф вызовов, блок-схемы ГОСТ 19.701)."
    if key == "hardware":
        return "Используемые технические средства: ПЭВМ с ОС Windows/Linux."
    if key == "call":
        return "Запуск программы осуществляется из командной строки или среды разработки; параметры — согласно руководству."
    if key == "input":
        return "Входные данные: исходные файлы проекта, параметры командной строки."
    if key == "output":
        return "Выходные данные: документация в форматах PDF, DOCX, TXT, JSON."
    if key == "identity":
        return f"Программа «{proj.name}». Обозначение документа по ЕСПД."
    if key == "notation":
        return "В тексте программы используются стандартные обозначения языка C++ и библиотеки Qt."
    if key == "sourcelist":
        return "Исходные файлы программы приведены в приложении."
    if key == "doclist":
        lines = ["Состав эксплуатационной документации на программу «%s»:" % proj.name]
        codes = []
        for code, doc in _import_docs():
            codes.append(code)
        lines.append(" — " + ", ".join(f"ГОСТ {c}" for c in codes) + " (разделы настоящего комплекта)")
        return " ".join(lines)
    if key == "general":
        return f"Наименование программы: «{proj.name}». Разработчик: {proj.author or '________'}."
    if key == "methods":
        return "Применяемые методы: объектно-ориентированное программирование, обработка данных, автоматическая генерация документов."
    if key == "architecture":
        return f"Архитектура: {len(proj.classes)} классов, {n_methods} методов, {len(proj.call_edges)} связей вызовов — модульная, с разделением на логические компоненты."
    if key == "io":
        return "Входные данные — исходные файлы; выходные — сформированные документы и схемы."
    if key == "volume":
        return f"Объём программы: {n_lines} строк исходного кода."
    if key == "messages":
        return "Сообщения оператору выводятся в консоль (сведения о сгенерированных документах) и в окно интерфейса."
    if key == "install":
        return (f"Установка программы «{proj.name}»: копирование дистрибутива, "
                "установка зависимостей (C++/Qt), настройка параметров через файл конфигурации.")
    if key == "programmer":
        return (f"Программа построена по модульному принципу: {len(proj.classes)} классов, "
                f"{n_methods} методов, {len(proj.functions)} свободных функций, "
                f"{len(proj.call_edges)} связей вызовов. Назначение модулей и функции "
                "приведены в приложении А.")
    if key == "terms":
        return glossary(proj)
    if key == "goal":
        return (f"Цель испытаний — подтвердить соответствие программы «{proj.name}» "
                "требованиям технического задания, работоспособность функций "
                f"({n_methods} методов) и корректность обработки данных.")
    if key == "testcases":
        funcs = proj.all_functions()
        rows = [
            f"Проверка работы функции {f.name}(): входные данные — "
            + (", ".join(f.params) if f.params else "без параметров")
            + ", ожидаемый результат — отсутствие сбоев и корректный вывод."
            for f in funcs[:12]
        ]
        return ("Тестовые примеры:\n  — " + "\n  — ".join(rows)
                + (f"\nВсего проверяется функций: {len(funcs)}." if len(funcs) > 12 else ""))
    if key == "procedures":
        return ("Испытания проводятся в порядке: проверка запуска, проверка "
                "функций по разделу «Тестовые примеры», проверка взаимодействия "
                "модулей, проверка документации. Результаты фиксируются в протоколе испытаний.")
    return ""


def glossary(proj: Project) -> str:
    """Термины и сокращения: идентификаторы программы и их назначение."""
    lines: list[str] = []
    for cls in proj.classes:
        desc = f"класс{(' «' + cls.base + '»') if cls.base else ''}"
        lines.append(f"{cls.name} — {desc}{('; ' + cls.comment) if cls.comment else ''}.")
    for fn in proj.functions:
        role = "главная функция" if fn.name == "main" else "функция"
        lines.append(f"{fn.name}() — {role}"
                     + (f"; {fn.brief}" if fn.brief else "")
                     + ".")
    for cls in proj.classes:
        for m in cls.methods:
            if not m.brief:
                continue
            kind = {"signal": "сигнал", "slot": "слот"}.get(m.kind, "метод")
            lines.append(f"{cls.name}::{m.name}() — {kind} «{m.brief}».")
    if proj.build.qt_modules:
        lines.append("Qt — библиотека классов; используются модули: "
                     + ", ".join(proj.build.qt_modules) + ".")
    return " ".join(lines)


# шапка листа регистрации изменений (ГОСТ 2.105)
REV_HEADERS = ("Номер изм.", "Номера листов",
               "Всего листов", "Номер документа", "Входящий №", "Подпись", "Дата")


def revision_rows() -> list[list[str]]:
    """Строки листа регистрации изменений (пока пустые)."""
    return [["", "", "", "", "", "", ""]]


def _import_docs():
    from ..styles.docs import DOCS
    return DOCS.items()
