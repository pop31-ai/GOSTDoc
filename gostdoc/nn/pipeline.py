"""Движок: прогон 23 нейросетей по проекту, вывод в консоль и в документ."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..parser.model import Project
from .feat import features
from .nets import networks, text_for


@dataclass
class NNResult:
    net_name: str
    category: str
    description: str
    score: float
    text: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def title(self) -> str:
        return f"{self.net_name} [{self.category}]"


def run_all(proj: Project) -> list[NNResult]:
    """Прямой проход всех сетей по проекту."""
    f = features(proj)
    results = []
    for net in networks():
        score = net.feed(f)
        results.append(NNResult(
            net_name=net.name,
            category=net.category,
            description=net.description,
            score=round(score, 4),
            text=text_for(net, proj, score),
            extra={"comment_density": round(f["comment_density"], 3),
                   "coverage": round(f["coverage"], 3)}))
    return results


def print_report(results: list[NNResult]) -> None:
    print("=" * 72)
    print("ГОСТДОК: нейросетевой анализ (23 сети)".center(72))
    print("=" * 72)
    current = None
    for r in results:
        if r.category != current:
            current = r.category
            print(f"\n--- {current.upper()} ---")
        print(f"  {r.net_name:<28} score={r.score:<8} {r.text}")
    print("=" * 72)
