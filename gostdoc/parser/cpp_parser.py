"""Лёгкий парсер C++/Qt: классы, методы, функции, вызовы.

Не заменяет полноценный AST-парсер (clang), но достаёт базовую
структуру программы для документации по ГОСТ 19.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import Class, Enum, Function, Project, TypeDef

_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_CLASS_RE = re.compile(r"^\s*(?:class|struct)\s+(\w+)\s*(?::\s*public\s+(\w+))?")
_ENUM_RE = re.compile(r"^\s*enum(?:\s+class)?\s+(\w+)?\s*\{")
_TYPEDEF_RE = re.compile(r"^\s*typedef\s+([\w:<>,&\*\s]+?)\s+(\w+)\s*;?\s*$")
_USING_RE = re.compile(r"^\s*using\s+(\w+)\s*=\s*([\w:<>,&\*\s]+?)\s*;?\s*$")
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(\w+)")
_DECL_RE = re.compile(
    r"^\s*(?:(virtual|static|inline|explicit|const|friend)\s+)*"
    r"([\w:<>,&\*]+)\s+(\w+)\s*\(([^;{]*)\)\s*(?:const)?\s*(?:override)?\s*([;{])"
)
_CTOR_RE = re.compile(r"^\s*(?:(virtual|static|inline|explicit|friend)\s+)*(~?\w+)\s*\(([^;{}]*)\)\s*([;{])")
_OPERATOR_RE = re.compile(r"^\s*(?:virtual\s+)?([\w:<>,&\*]+)\s+operator\s*(\S+)\s*\(([^;{}]*)\)\s*(?:const)?\s*(?:override)?\s*[;{]")
_FIELD_RE = re.compile(r"^\s*([\w:<>,&\*]+)\s+(\w+)\s*(?:\[[^\]]*\])?\s*[;=]")
_COMMENT_BLOCK_RE = re.compile(r"/\*(.*?)\*/", re.S)
_COMMENT_LINE_RE = re.compile(r"//.*$", re.M)
_LITERALS_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\\\']|\\.)*\'')
_ACCESS_RE = re.compile(r"\b(public|private|protected|signals|slots|Q_SIGNALS|Q_SLOTS)\s*:")
_CONNECT_RE = re.compile(
    r"connect\s*\(\s*([\w]+)[^,]*,\s*(?:SIGNAL\s*\(\s*([\w]+)|\&[\w]+::([\w]+))\s*\)?[^,]*,\s*([\w]+)[^,]*,\s*(?:SLOT\s*\(\s*([\w]+)|\&[\w]+::([\w]+))\s*\)?")
_CONNECT_Q5_RE = re.compile(r"connect\s*\(\s*([\w]+)\s*,\s*\&([\w:]+)::([\w]+)\s*,\s*([\w]+)\s*,\s*\&([\w:]+)::([\w]+)\s*\)")

_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "sizeof", "new",
             "delete", "static_cast", "const_cast", "dynamic_cast",
             "reinterpret_cast", "emit", "connect", "disconnect", "Q_EMIT",
             "slots", "signals", "public", "private", "protected", "throw",
             "goto", "typename", "template", "alignof", "decltype", "noexcept"}


def _strip_literals(src: str) -> str:
    return _LITERALS_RE.sub("", src)


def _extract_call_names(block: str) -> list[str]:
    """Имена функций, вызванных в теле функции."""
    body = _COMMENT_LINE_RE.sub("", block)
    body = _strip_literals(body)
    names: list[str] = []
    for m in _CALL_RE.finditer(body):
        name = m.group(1)
        if name in _KEYWORDS or "::" in name:
            continue
        if name not in names:
            names.append(name)
    return names


_COND_RE = re.compile(r"\b(if|while|for)\s*\(([^()]*)\)")


def _extract_conditions(block: str) -> list[str]:
    """Условия ветвлений/циклов в теле функции (ГОСТ 19.701 — ромбы)."""
    body = _COMMENT_LINE_RE.sub("", block)
    body = _strip_literals(body)
    out: list[str] = []
    for m in _COND_RE.finditer(body):
        text = f"{m.group(1)} {m.group(2)}".strip()
        if text not in out:
            out.append(text)
    return out


def _extract_connections(block: str) -> list[tuple[str, str, str, str]]:
    """Пары (отправитель, получатель, сигнал, слот) из connect() в теле."""
    body = _COMMENT_LINE_RE.sub("", block)
    body = _strip_literals(body)
    out: list[tuple[str, str, str, str]] = []
    for m in _CONNECT_RE.finditer(body):
        sender, recv = m.group(1), m.group(4)
        sig = m.group(2) or m.group(3)
        slot = m.group(5) or m.group(6)
        if sender and recv and sig and slot:
            pair = (sender, recv, sig, slot)
            if pair not in out:
                out.append(pair)
    for m in _CONNECT_Q5_RE.finditer(body):
        pair = (m.group(1), m.group(4), m.group(3), m.group(6))
        if pair not in out:
            out.append(pair)
    return out


def _parse_params(params: str) -> list[str]:
    return [p.strip() for p in params.split(",") if p.strip() and p.strip() != "..."]


_TAG_NEXT = r"(?!\s@[a-z]+\b)"
_DOXY_TEMPERED = r"((?:" + _TAG_NEXT + r".)*)"
_DOXY_BRIEF_RE = re.compile(r"@brief\s+" + _DOXY_TEMPERED, re.I | re.S)
_DOXY_PARAM_RE = re.compile(
    r"@param(?:\[[^\]]+\])?\s+(\w+)\s*:?\s*" + _DOXY_TEMPERED, re.I)
_DOXY_RETURN_RE = re.compile(r"@return\s+" + _DOXY_TEMPERED, re.I)


def _parse_doxygen(comment: str) -> tuple[str, dict[str, str], str]:
    """Извлекает Doxygen-поля @brief, @param, @return из комментария."""
    brief = ""
    m = _DOXY_BRIEF_RE.search(comment)
    if m:
        brief = " ".join(m.group(1).split())
    else:
        first = re.split(r"\s@[a-z]+\b", comment, maxsplit=1)[0]
        brief = " ".join(first.split())
    params: dict[str, str] = {}
    for m in _DOXY_PARAM_RE.finditer(comment):
        params[m.group(1)] = " ".join(m.group(2).split())
    returns = ""
    m = _DOXY_RETURN_RE.search(comment)
    if m:
        returns = " ".join(m.group(1).split())
    return brief, params, returns


def _last_comment(raw_lines: list[str], idx: int) -> str:
    """Комментарий, стоящий над строкой idx (строки /— // или /**)."""
    out: list[str] = []
    i = idx - 1
    while i >= 0:
        line = raw_lines[i].strip()
        if not line:
            break
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            out.append(line.lstrip("/").lstrip("*").strip())
            i -= 1
        elif out:
            break
        else:
            break
    return " ".join(reversed(out)).strip()


def _strip_block_comments(raw: str) -> str:
    """Удаляет блочные комментарии, сохраняя число строк (нужно для
    совпадения номеров строк со строками исходника)."""

    def repl(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")

    return _COMMENT_BLOCK_RE.sub(repl, raw)


def _balance_index(lines: list[str], start: int) -> int:
    """Индекс строки, закрывающей фигурную скобку, открытую на start."""
    depth = 0
    for j in range(start, len(lines)):
        opens, closes = lines[j].count("{"), lines[j].count("}")
        depth += opens - closes
        if j > start and depth <= 0:
            return j
        if j == start and opens == closes and opens:
            return j
    return len(lines) - 1


def parse_file(path: str | Path) -> tuple[list[Class], list[Enum], list[TypeDef], list[str]]:
    """Парсит один файл: классы, перечисления, typedef'ы, пространства имён."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    src = _strip_block_comments(raw)
    lines = src.splitlines()
    raw_lines = raw.splitlines()

    classes: list[Class] = []
    enums: list[Enum] = []
    typedefs: list[TypeDef] = []
    namespaces: list[str] = []

    # пространства имён
    for k, line in enumerate(lines):
        m = _NAMESPACE_RE.match(line)
        if m and m.group(1) not in namespaces:
            namespaces.append(m.group(1))

    # typedef / using
    for k, line in enumerate(lines):
        m = _TYPEDEF_RE.match(line)
        if m:
            typedefs.append(TypeDef(name=m.group(2).strip(),
                                   aliased=m.group(1).strip(), file=path.name, line=k + 1))
            continue
        m = _USING_RE.match(line)
        if m:
            typedefs.append(TypeDef(name=m.group(1).strip(),
                                   aliased=m.group(2).strip(), file=path.name, line=k + 1))

    # перечисления
    for k, line in enumerate(lines):
        m = _ENUM_RE.match(line)
        if not m:
            continue
        body_end = _balance_index(lines, k)
        if body_end == k:
            inner = line[line.find("{") + 1:line.rfind("}")]
        else:
            inner = "\n".join(lines[k + 1:body_end])
        values = [v.strip() for v in inner.split(",") if v.strip()]
        enums.append(Enum(name=m.group(1) or "", file=path.name, line=k + 1,
                          values=values, comment=_last_comment(raw_lines, k)))
        i = body_end + 1

    i = 0
    while i < len(lines):
        m = _CLASS_RE.match(lines[i])
        if not m:
            i += 1
            continue
        name, base = m.group(1), m.group(2) or ""
        cls = Class(name=name, base=base, file=path.name, line=i + 1,
                    comment=_last_comment(raw_lines, i))
        body_end = _balance_index(lines, i)
        body = "\n".join(lines[i + 1:body_end])
        cls.fields, cls.methods = _parse_class_body(body, path.name, raw_lines, i + 1)
        classes.append(cls)
        i = body_end + 1
    return classes, enums, typedefs, namespaces


def _parse_class_body(body: str, file: str, src_lines: list[str],
                      body_start_line: int) -> tuple[list[str], list[Function]]:
    fields: list[str] = []
    methods: list[Function] = []

    # разбиваем по модификаторам доступа, считая offset строки
    chunks = _ACCESS_RE.split(body)
    chunk_lines = [c.count("\n") for c in chunks]
    running = 0
    kind = "method"
    for idx, chunk in enumerate(chunks):
        if idx % 2 == 0:
            body_lines = chunk.splitlines()
            for k, line in enumerate(body_lines):
                lineno = body_start_line + running + k
                mm = _DECL_RE.match(line)
                if mm:
                    comment = _last_comment(src_lines, lineno)
                    brief, params_doc, returns = _parse_doxygen(comment)
                    func = Function(
                        name=mm.group(3),
                        return_type=(mm.group(1) + " " if mm.group(1) else "") + mm.group(2).strip(),
                        params=_parse_params(mm.group(4)),
                        file=file, line=lineno, is_method=True,
                        comment=comment, kind=kind,
                        brief=brief, params_doc=params_doc, returns=returns)
                    if mm.group(5) == "{":
                        body_start = body_lines.index(line, k)
                        # считаем конец тела
                        depth = 0
                        bl = body_lines
                        j = k
                        while j < len(bl):
                            depth += bl[j].count("{") - bl[j].count("}")
                            if depth == 0 and j > k:
                                break
                            j += 1
                        body_txt = "\n".join(bl[k + 1:j])
                        func.calls = _extract_call_names(body_txt)
                        func.conditions = _extract_conditions(body_txt)
                        func.connections = _extract_connections(body_txt)
                    methods.append(func)
                    continue
                cm = _CTOR_RE.match(line)
                if cm and not _DECL_RE.match(line):
                    comment = _last_comment(src_lines, lineno)
                    brief, params_doc, returns = _parse_doxygen(comment)
                    func = Function(
                        name=cm.group(2),
                        return_type=(cm.group(1) + " " if cm.group(1) else ""),
                        params=_parse_params(cm.group(3)),
                        file=file, line=lineno, is_method=True,
                        comment=comment, kind=kind,
                        brief=brief, params_doc=params_doc, returns=returns)
                    methods.append(func)
                    continue
                om = _OPERATOR_RE.match(line)
                if om:
                    comment = _last_comment(src_lines, lineno)
                    brief, params_doc, returns = _parse_doxygen(comment)
                    func = Function(
                        name=f"operator{om.group(2).strip()}",
                        return_type=om.group(1).strip(),
                        params=_parse_params(om.group(3)),
                        file=file, line=lineno, is_method=True,
                        comment=comment, kind=kind,
                        brief=brief, params_doc=params_doc, returns=returns)
                    methods.append(func)
                    continue
                fm = _FIELD_RE.match(line)
                if fm and "(" not in fm.group(1) and fm.group(2):
                    fields.append(f"{fm.group(1).strip()} {fm.group(2).strip()}")
        else:
            label = chunk.strip()
            if "signals" in label or "Q_SIGNALS" in label:
                kind = "signal"
            elif "slots" in label or "Q_SLOTS" in label:
                kind = "slot"
            else:
                kind = "method"
        if idx < len(chunk_lines):
            running += chunk_lines[idx]
    return fields, methods


def parse_project(src_dir: str | Path, name: str = "", author: str = "",
                  organisation: str = "", comment: str = "") -> Project:
    """Рекурсивно парсит все C++-исходники в каталоге."""
    src_dir = Path(src_dir)
    from .build_parser import parse_build

    build = parse_build(src_dir)
    proj = Project(name=name or build.name or src_dir.name, author=author,
                   organisation=organisation, comment=comment, build=build)
    suffixes = (".cpp", ".cc", ".h", ".hpp")
    files = sorted(p for p in src_dir.rglob("*") if p.suffix.lower() in suffixes)
    for path in files:
        proj.sources.append(str(path))
        classes, enums, typedefs, namespaces = parse_file(path)
        proj.classes.extend(classes)
        proj.enums.extend(enums)
        proj.typedefs.extend(typedefs)
        for ns in namespaces:
            if ns not in proj.namespaces:
                proj.namespaces.append(ns)

    # свободные функции и определения методов из cpp-файлов
    for path in files:
        if path.suffix.lower() not in (".cpp", ".cc"):
            continue
        text = _COMMENT_BLOCK_RE.sub("", path.read_text(encoding="utf-8", errors="ignore"))
        text = _COMMENT_LINE_RE.sub("", text)
        for m in re.finditer(
                r"^([\w:<>,&\*]+)\s+(\w+)::(\w+)\s*\(([^;{}]*)\)\s*(?:const)?\s*\{(.*?)\n\}",
                text, re.M | re.S):
            cls_name, fname, calls = m.group(2), m.group(3), _extract_call_names(m.group(5))
            for cls in proj.classes:
                if cls.name == cls_name:
                    for f in cls.methods:
                        if f.name == fname:
                            f.calls = calls
                            f.conditions = _extract_conditions(m.group(5))
                            f.connections = _extract_connections(m.group(5))
                            f.file = path.name
        for m in re.finditer(
                r"^([\w:<>,&\*]+)\s+(\w+)\s*\(([^;{}]*)\)\s*(?:const)?\s*\{(.*?)\n\}",
                text, re.M | re.S):
            fname = m.group(2)
            if "::" in fname or fname in {f.name for f in proj.functions}:
                continue
            proj.functions.append(Function(
                name=fname, return_type=m.group(1).strip(),
                params=_parse_params(m.group(3)), file=path.name,
                is_method=False, calls=_extract_call_names(m.group(4)),
                conditions=_extract_conditions(m.group(4)),
                connections=_extract_connections(m.group(4))))

    # собираем граф вызовов
    known = {f.name for f in proj.all_functions()}
    edges: list[tuple[str, str]] = []
    for f in proj.all_functions():
        for callee in f.calls:
            if callee in known and callee != f.name:
                edges.append((f.name, callee))
    proj.call_edges = edges
    return proj
