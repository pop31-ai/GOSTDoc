"""Нейросети GOSTDoc: 23 модели для документации по ГОСТ."""

from .nets import networks, text_for
from .pipeline import NNResult, run_all, print_report
from .net import Net

__all__ = ["networks", "text_for", "run_all", "print_report", "Net", "NNResult"]
