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
        return "Требования к техническим средствам: ПЭВМ, ОС Windows/Linux, среда выполнения C++/Qt."
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
    return ""


def _import_docs():
    from ..styles.docs import DOCS
    return DOCS.items()
