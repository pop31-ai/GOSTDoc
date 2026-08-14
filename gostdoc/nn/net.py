"""Простая нейросеть GOSTDoc: линейный регрессор/классификатор с
откалиброванными весами (weights.py). Обучение — в консоли (train.py).
"""

from __future__ import annotations

from typing import Any


class Net:
    """Минимальная нейросеть: входы -> взвешенная сумма -> функция активации."""

    def __init__(self, name: str, category: str, description: str,
                 weights: dict[str, float] | None = None, bias: float = 0.0,
                 activation: str = "linear"):
        self.name = name
        self.category = category
        self.description = description
        self.weights = weights or {}
        self.bias = bias
        self.activation = activation

    def feed(self, features: dict[str, float]) -> float:
        """Прямой проход: z = sum(w_i * x_i) + b, затем активация."""
        z = self.bias + sum(self.weights.get(k, 0.0) * features.get(k, 0.0)
                            for k in self.weights)
        if self.activation == "sigmoid":
            return 1.0 / (1.0 + __import__("math").exp(-z))
        if self.activation == "relu":
            return max(0.0, z)
        if self.activation == "tanh":
            return __import__("math").tanh(z)
        return z

    def predict(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Интерфейс для документатора. По умолчанию — взвешенная сумма."""
        return {"score": round(self.feed(inputs), 4), "inputs": dict(inputs)}
