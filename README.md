# GOSTDoc

Генератор документации по ГОСТ 19 для программ на C++/Qt.
Автоматически разбирает исходники, строит схемы (диаграммы классов,
граф вызовов, блок-схемы функций) и формирует документы по
ГОСТ 19.402, ГОСТ 2.105, ГОСТ 19.701 в форматах **PDF, DOCX, TXT**.

## Установка

```bash
git clone https://github.com/pop31-ai/GOSTDoc.git
cd GOSTDoc
pip install -e .
```

Опционально: [Graphviz](https://graphviz.org/download/) для схем.
Без него схемы строит собственный рендер на Pillow (fallback) —
диаграммы классов, граф вызовов и блок-схемы генерируются всегда.

## Использование

```bash
gostdoc --project ./src --out ./docs --format pdf,docx,txt \
        --name "Моя программа" --author "Иванов И.И." \
        --organisation "ООО «Пример»" --nn
```

Флаг `--nn` запускает 23 нейросети, которые анализируют код и добавляют
в документ приложение «Результаты нейросетевого анализа» (схемы, оценки
сложности, покрытие комментариями, соответствие ГОСТ, тест-кейсы,
трудозатраты и др.).

Переобучение нейросетей в консоли:

```bash
python -m gostdoc.nn.train --data data.csv \
       --projects examples/sample examples/alt \
       --out gostdoc/nn/weights.py
```

Параметры:

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `--project` / `-p` | `.` | каталог с `*.cpp/*.h/*.hpp` |
| `--out` / `-o` | `./docs` | каталог результата |
| `--format` / `-f` | `pdf,docx,txt` | форматы: pdf, docx, txt, html, json |
| `--name` | имя каталога | название программы |
| `--author` | пусто | разработчик |
| `--organisation` | пусто | организация |
| `--comment` | пусто | аннотация |
| `--nn` | выкл | запуск 23 нейросетей анализа |
| `--doctype` | `19.402` | тип документа: `19.401`, `19.402`, `19.403`, `19.404`, `19.504`, `19.505` или `all` |
| `--zip` | выкл | упаковать все сгенерированные документы в ZIP |

Тип `all` генерирует полный комплект ЕСПД:

| Код | Документ |
|---|---|
| ГОСТ 19.401 | Текст программы |
| ГОСТ 19.402 | Описание программы |
| ГОСТ 19.403 | Ведомость эксплуатационных документов |
| ГОСТ 19.404 | Пояснительная записка |
| ГОСТ 19.504 | Руководство программиста |
| ГОСТ 19.505 | Руководство оператора |

```bash
gostdoc --project ./src --out ./docs --doctype all --format pdf,docx
```

## Qt-интерфейс (GOSTDoc Studio)

```bash
pip install -e ".[gui]"
gostdoc-gui
```

Окно: каталог исходников, вывод, название/автор/организация, форматы,
флаг нейросетей и лог генерации.

## Нейросети (23 модели)

| Категория | Сети |
|---|---|
| Генерация текста | ClassCommenter, MethodSummarizer, ProgramAnnotator, SectionWriter, GlossaryExtractor, TitlePageGenerator |
| Анализ кода | CodeClassifier, ComplexityEstimator, DependencyAnalyzer, DuplicateDetector, ReadabilityScorer, NamingQualityChecker, CommentCoverageAnalyzer, QtSignalSlotMatcher, FunctionRoleTagger |
| Схемы и структура | FlowchartGenerator, ClassDiagramBuilder, CallGraphNet, ArchitectureCluster, SequenceDiagramGenerator |
| Контроль качества | GOSTComplianceChecker, TestcaseGenerator, EffortEstimator |

Модели — линейные/логистические сети с откалиброванными весами
(`gostdoc/nn/weights.py`), без ML-зависимостей. Вход: признаки проекта
(число классов, функций, вызовов, строк, комментариев и т.п.).

## Оформление по ГОСТ

- Шрифт Times New Roman 14 пт, межстрочный интервал 1.5;
- поля: левое 30 мм, правое 10 мм, верх/низ 20 мм (ГОСТ 2.105);
- абзацный отступ 1.25 см;
- титульный лист, аннотация, содержание, нумерованные разделы;
- номера страниц по ГОСТ 2.105 (по центру нижней части листа);
- схемы алгоритмов по нотации ГОСТ 19.701 (Graphviz или собственный рендер Pillow);
- блок-схемы с ветвлениями: вызовы — прямоугольники, условия if/while/for — ромбы;
- диаграммы последовательности: цепочки вызовов от точки входа (main и свободных функций);
- Qt: разбор сигналов/слотов и связей `connect()` с включением в структуру программы;
- приложение «Текст программы» (ГОСТ 19.401) с нумерованными исходниками;
- JSON-экспорт структуры программы и результатов анализа;
- HTML-рендер в один файл (схемы встраиваются как base64);
- пакетирование комплекта в ZIP (`--zip`);
- лист регистрации изменений (ГОСТ 2.105) в конце каждого документа;
- Doxygen-комментарии: `@brief`, `@param`, `@return` попадают в структуру программы;
- разбор: классы, методы, конструкторы/деструкторы, перегрузка операторов,
  перечисления (enum), typedef/using, пространства имён, условия и вызовы.

## Структура

```
gostdoc/
  cli.py           # точка входа
  parser/          # разбор C++/Qt (классы, методы, вызовы, Qt-сигналы/слоты)
  grapher/         # схемы (Graphviz DOT + fallback на Pillow)
  styles/          # константы ГОСТ-оформления
  render/          # рендеры: docx, pdf, txt
  nn/              # 23 нейросети + обучение (net, nets, feat, train, pipeline)
examples/          # тестовые C++/Qt проекты
tests/             # юнит-тесты
```

## Тесты

```bash
pip install -e .[dev]
pytest
```

## Сборка дистрибутива

```bash
python -m build        # создаёт sdist + wheel
pip install dist/gostdoc-0.2.0-py3-none-any.whl
```

Standalone `.exe` (Windows, без Python):

```bash
build.bat
dist\gostdoc.exe --version
```

## Конфигурация

Файл `.gostdoc.json` в текущем каталоге (или `--config путь`):

```json
{
  "project": "./src",
  "out": "./docs",
  "format": "pdf,docx,txt,json",
  "name": "Моя программа",
  "author": "Иванов И.И.",
  "organisation": "ООО «Пример»",
  "comment": "Аннотация",
  "nn": true
}
```

Запуск без аргументов использует конфиг из текущего каталога.

## Пример

```bash
gostdoc --project examples/sample --out docs
```
