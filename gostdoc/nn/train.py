"""Обучение/калибровка нейросетей в консоли.

Считывает data.csv (колонка target — желаемый выход), подгоняет смещение
(bias) каждой сети методом наименьших квадратов и сохраняет веса в weights.py.

Пример:
    python -m gostdoc.nn.train --data data.csv --out gostdoc/nn/weights.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .feat import features
from .nets import networks
from ..parser.cpp_parser import parse_project


def _fit_bias(targets: list[float], scores: list[float]) -> float:
    """bias, минимизирующий sum((score+b-target)^2)."""
    n = len(scores)
    if n == 0:
        return 0.0
    mean = sum(scores) / n
    tmean = sum(targets) / n
    return tmean - mean


def train(data_csv: Path, projects: list[Path], out: Path) -> dict[str, dict]:
    rows = list(csv.DictReader(data_csv.open(encoding="utf-8")))
    proj_cache: dict[int, Project] = {}
    for r in rows:
        idx = int(r["project"])
        if idx not in proj_cache:
            proj_cache[idx] = parse_project(projects[idx])
    nets = networks()
    calibrated: dict[str, dict] = {}
    for net in nets:
        targets, scores = [], []
        for row in rows:
            if row.get("net") not in (net.name, "*"):
                continue
            proj = proj_cache[int(row["project"])]
            target = float(row["target"])
            f = features(proj)
            scores.append(net.feed(f) - net.bias)
            targets.append(target)
        bias = _fit_bias(targets, scores)
        calibrated[net.name] = {"bias": round(bias, 4), "weights": net.weights,
                                "activation": net.activation,
                                "category": net.category}
    _write_weights(out, calibrated)
    return calibrated


def _write_weights(out: Path, data: dict) -> None:
    lines = ['"""Автосгенерированные веса нейросетей (см. train.py)."""', ""]
    for name, v in sorted(data.items()):
        lines.append(f'{name} = {v!r}')
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="gostdoc-train", description="Калибровка нейросетей ГОСТ")
    ap.add_argument("--data", default="data.csv", help="CSV: project,target")
    ap.add_argument("--projects", nargs="*", default=["examples/sample"],
                    help="каталоги примеров проектов")
    ap.add_argument("--out", default=str(Path("gostdoc/nn/weights.py")))
    args = ap.parse_args(argv)

    projs = [Path(p) for p in args.projects]
    calibrated = train(Path(args.data), projs, Path(args.out))
    print(f"Откалибровано сетей: {len(calibrated)}")
    for name, v in calibrated.items():
        print(f"  {name}: bias={v['bias']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
