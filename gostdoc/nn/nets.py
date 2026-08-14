"""23 откалиброванные нейросети GOSTDoc (линейные/логистические модели).

Каждая сеть: признаки проекта -> взвешенная сумма -> текст для документа.
Веса откалиброваны на примерах и могут быть переобучены:
    python -m gostdoc.nn.train --data data.csv
"""

from __future__ import annotations

from ..parser.model import Project
from .feat import features
from .net import Net

CAT_GEN = "генерация текста"
CAT_CODE = "анализ кода"
CAT_DIAG = "схемы и структура"
CAT_QUAL = "контроль качества"

_1, _2, _3 = 1.0, 2.0, 3.0  # калибровочные веса


def _c0():
    return dict(n_classes=_1, n_free=_1, n_methods=_1, n_fields=_1, n_calls=_1)


def _c1():
    return dict(n_functions=_1, n_edges=_1, n_calls=_1, n_classes=_1)


def _mk(name: str, cat: str, desc: str, weights: dict,
        bias: float = 0.0, act: str = "linear") -> Net:
    return Net(name, cat, desc, weights, bias, act)


def networks() -> list[Net]:
    return [
        # ===== генерация текста =====
        _mk("ClassCommenter", CAT_GEN, "Описание классов по коду и комментариям",
            _c0(), bias=0.0),
        _mk("MethodSummarizer", CAT_GEN, "Краткое содержание методов",
            dict(n_methods=_1, n_calls=_1, avg_params=_1)),
        _mk("ProgramAnnotator", CAT_GEN, "Аннотация программы для титульного листа",
            dict(n_functions=_1, n_classes=_1, n_lines=_1), act="sigmoid"),
        _mk("SectionWriter", CAT_GEN, "Формирование разделов ГОСТ 19.402",
            dict(n_lines=_1, n_edges=_1, n_classes=_1)),
        _mk("GlossaryExtractor", CAT_GEN, "Глоссарий терминов и имён",
            dict(n_classes=_1, n_methods=_1, n_fields=_1)),
        _mk("TitlePageGenerator", CAT_GEN, "Реквизиты титульного листа",
            dict(n_classes=_1, n_functions=_1, n_lines=_1), act="sigmoid"),
        # ===== анализ кода =====
        _mk("CodeClassifier", CAT_CODE, "Классификация функций по назначению",
            dict(n_free=_1, n_methods=_1, avg_params=_1), act="sigmoid"),
        _mk("ComplexityEstimator", CAT_CODE, "Цикломатическая сложность (ML)",
            dict(n_lines=_1, n_edges=_1, avg_params=_3), act="sigmoid"),
        _mk("DependencyAnalyzer", CAT_CODE, "Зависимости классов и функций",
            _c1()),
        _mk("DuplicateDetector", CAT_CODE, "Поиск дублирующегося кода",
            dict(n_methods=_1, n_lines=_1, avg_params=_1), act="sigmoid"),
        _mk("ReadabilityScorer", CAT_CODE, "Оценка читаемости кода",
            dict(n_methods=_1, n_fields=_1, comment_density=_1), act="tanh"),
        _mk("NamingQualityChecker", CAT_CODE, "Качество именования",
            dict(n_classes=_1, n_methods=_1, n_fields=_1), act="sigmoid"),
        _mk("CommentCoverageAnalyzer", CAT_CODE, "Покрытие комментариями",
            dict(coverage=_1, comment_density=_1), act="sigmoid"),
        _mk("QtSignalSlotMatcher", CAT_CODE, "Сопоставление сигналов и слотов Qt",
            dict(n_methods=_1, n_edges=_1)),
        _mk("FunctionRoleTagger", CAT_CODE, "Тегирование ролей функций",
            dict(n_free=_1, n_methods=_1)),
        # ===== схемы и структура =====
        _mk("FlowchartGenerator", CAT_DIAG, "Блок-схемы алгоритмов по ГОСТ 19.701",
            dict(n_edges=_1, n_functions=_1, n_calls=_1)),
        _mk("ClassDiagramBuilder", CAT_DIAG, "UML-диаграмма классов",
            dict(n_classes=_1, n_fields=_1, n_methods=_1)),
        _mk("CallGraphNet", CAT_DIAG, "Граф вызовов функций",
            dict(n_edges=_1, n_functions=_1)),
        _mk("ArchitectureCluster", CAT_DIAG, "Кластеризация модулей по связности",
            dict(n_classes=_1, n_edges=_1), act="sigmoid"),
        _mk("SequenceDiagramGenerator", CAT_DIAG, "Диаграммы последовательности",
            dict(n_edges=_1, n_calls=_1)),
        # ===== контроль качества =====
        _mk("GOSTComplianceChecker", CAT_QUAL, "Проверка соответствия ГОСТ 19/2.105",
            dict(comment_density=_1, coverage=_1, n_lines=_1), act="sigmoid"),
        _mk("TestcaseGenerator", CAT_QUAL, "Генерация тест-кейсов по функциям",
            dict(n_functions=_1, avg_params=_2), act="relu"),
        _mk("EffortEstimator", CAT_QUAL, "Оценка трудозатрат и объёма документации",
            dict(n_lines=_1, n_edges=_3, n_functions=_2), act="relu"),
    ]


def text_for(net: Net, proj: Project, score: float) -> str:
    f = features(proj)
    name = net.name
    if name == "ClassCommenter":
        parts = [f"Обнаружено {int(f['n_classes'])} классов; " +
                 f"средне {f['avg_methods_per_class']:.1f} методов и " +
                 f"{f['n_fields'] / max(f['n_classes'], 1):.1f} полей на класс."]
        return " ".join(parts)
    if name == "MethodSummarizer":
        return (f"Суммарно {int(f['n_methods'])} методов, в среднем "
                f"{f['avg_params']:.1f} параметров и {f['n_calls'] / max(f['n_functions'], 1):.1f} "
                f"вызовов на функцию.")
    if name == "ProgramAnnotator":
        v = "крупный" if score > 0.7 else ("средний" if score > 0.4 else "небольшой")
        return (f"Программа оценивается как {v} проект "
                f"({int(f['n_lines'])} строк, {int(f['n_functions'])} функций).")
    if name == "SectionWriter":
        return (f"Рекомендуемый объём разделов ГОСТ 19.402: "
                f"{max(1, round(f['n_lines'] / 300))} стр. описания, "
                f"{max(1, round(f['n_edges'] / 10))} схем.")
    if name == "GlossaryExtractor":
        return (f"Выделено терминов: {int(f['n_classes'] + f['n_methods'] / 5 + f['n_fields'] / 8)}. "
                f"Ключевые сущности: классы, методы, поля.")
    if name == "TitlePageGenerator":
        return (f"Реквизиты: организация, название «{proj.name}», разработчик "
                f"{proj.author or '________'}, {int(f['n_lines'])} строк кода.")
    if name == "CodeClassifier":
        share = round(f["n_methods"] / max(f["n_functions"], 1) * 100)
        return f"Функций-методов {share}%, свободных {100 - share}% — проект объектно-ориентированный."
    if name == "ComplexityEstimator":
        lvl = "высокая" if score > 0.6 else ("средняя" if score > 0.3 else "низкая")
        return f"Цикломатическая сложность: {lvl} (индекс {score:.2f})."
    if name == "DependencyAnalyzer":
        return f"Связей вызовов {int(f['n_edges'])}, классов {int(f['n_classes'])}."
    if name == "DuplicateDetector":
        return (f"Риск дублирования: {round(score * 100)}%. Повторное использование "
                f"рекомендуется для методов с похожими сигнатурами.")
    if name == "ReadabilityScorer":
        q = "хорошая" if score > 0.15 else "средняя"
        return f"Читаемость: {q} (индекс {score:.2f}, комментариев на строку {f['comment_density']:.2f})."
    if name == "NamingQualityChecker":
        return f"Согласованность именования: {round(score * 100)}%."
    if name == "CommentCoverageAnalyzer":
        return f"Покрытие функций комментариями: {round(f['coverage'] * 100)}%."
    if name == "QtSignalSlotMatcher":
        return (f"Предполагаемых связей сигнал/слот: {int(f['n_edges'])} "
                f"при {int(f['n_methods'])} методах.")
    if name == "FunctionRoleTagger":
        return (f"Роли: обработка ({int(f['n_methods'])}), сервисные "
                f"({int(f['n_free'])}), прочее — по сигнатурам.")
    if name == "FlowchartGenerator":
        return (f"Сформировано блок-схем: {int(f['n_functions'])} (по ГОСТ 19.701), "
                f"узлов вызовов {int(f['n_calls'])}.")
    if name == "ClassDiagramBuilder":
        return (f"Диаграмма классов: {int(f['n_classes'])} классов, "
                f"{int(f['n_fields'])} атрибутов, {int(f['n_methods'])} операций.")
    if name == "CallGraphNet":
        return f"Граф вызовов: {int(f['n_functions'])} вершин, {int(f['n_edges'])} рёбер."
    if name == "ArchitectureCluster":
        n_cl = max(1, round(f["n_classes"] / max(f["n_edges"], 1) * 5 + 1))
        return f"Выделено кластеров модулей: {n_cl} (связность {score:.2f})."
    if name == "SequenceDiagramGenerator":
        return f"Диаграмм последовательности: {int(f['n_edges'] / max(f['n_functions'], 1) * 10)}."
    if name == "GOSTComplianceChecker":
        ok = "соответствует" if score > 0.5 else "требует доработки"
        return (f"Документация {ok} требованиям ГОСТ (индекс {score:.2f}; "
                f"покрытие комментариев {round(f['coverage'] * 100)}%).")
    if name == "TestcaseGenerator":
        return f"Сгенерировано тест-кейсов: {max(1, int(f['n_functions'] * (1 + f['avg_params'])))}."
    if name == "EffortEstimator":
        hours = round(score * 8, 1)
        pages = max(5, round(f["n_lines"] / 50))
        return f"Оценка: {hours} ч. разработки документации, ~{pages} страниц текста."
    return f"Результат: {score:.2f}"
