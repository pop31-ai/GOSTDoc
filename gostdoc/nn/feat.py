"""Извлечение признаков проекта для нейросетей."""

from __future__ import annotations

from pathlib import Path

from ..parser.model import Project


def features(proj: Project) -> dict[str, float]:
    funcs = proj.all_functions()
    n_methods = sum(1 for f in funcs if f.is_method)
    n_free = len(proj.functions)
    n_classes = len(proj.classes)
    n_fields = sum(len(c.fields) for c in proj.classes)
    avg_params = (sum(len(f.params) for f in funcs) / len(funcs)) if funcs else 0.0
    calls = sum(len(f.calls) for f in funcs)
    n_lines = sum(1 for s in proj.sources for _ in
                  Path(s).read_text(encoding="utf-8", errors="ignore").splitlines())
    n_comments = sum(
        sum(1 for line in Path(s).read_text(encoding="utf-8", errors="ignore")
            .splitlines() if line.strip().startswith("//")
            or line.strip().startswith("/*") or line.strip().startswith("*"))
        for s in proj.sources)
    n_edges = len(proj.call_edges)
    documented = sum(1 for f in funcs if f.comment)
    return {
        "n_classes": float(n_classes),
        "n_free": float(n_free),
        "n_methods": float(n_methods),
        "n_fields": float(n_fields),
        "n_functions": float(len(funcs)),
        "n_lines": float(n_lines),
        "n_comments": float(n_comments),
        "n_calls": float(calls),
        "n_edges": float(n_edges),
        "n_documented": float(documented),
        "avg_params": float(avg_params),
        "comment_density": (n_comments / n_lines) if n_lines else 0.0,
        "coverage": (documented / len(funcs)) if funcs else 0.0,
        "avg_methods_per_class": (n_methods / n_classes) if n_classes else 0.0,
    }
