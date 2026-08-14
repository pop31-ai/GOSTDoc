"""Модель данных, описывающая структуру программы."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Function:
    name: str
    return_type: str = "void"
    params: list[str] = field(default_factory=list)
    file: str = ""
    line: int = 0
    is_method: bool = False
    comment: str = ""
    calls: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    kind: str = "method"  # method / signal / slot
    connections: list[tuple[str, str, str, str]] = field(default_factory=list)


@dataclass
class Class:
    name: str
    base: str = ""
    file: str = ""
    line: int = 0
    comment: str = ""
    fields: list[str] = field(default_factory=list)
    methods: list[Function] = field(default_factory=list)


@dataclass
class Enum:
    name: str
    file: str = ""
    line: int = 0
    values: list[str] = field(default_factory=list)
    comment: str = ""


@dataclass
class TypeDef:
    name: str
    aliased: str = ""
    file: str = ""
    line: int = 0


@dataclass
class Project:
    name: str
    author: str = ""
    organisation: str = ""
    comment: str = ""
    sources: list[str] = field(default_factory=list)
    classes: list[Class] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    call_edges: list[tuple[str, str]] = field(default_factory=list)
    nn_results: list = field(default_factory=list)
    enums: list[Enum] = field(default_factory=list)
    typedefs: list[TypeDef] = field(default_factory=list)
    namespaces: list[str] = field(default_factory=list)

    def all_functions(self) -> list[Function]:
        out = list(self.functions)
        for cls in self.classes:
            out.extend(cls.methods)
        return out
