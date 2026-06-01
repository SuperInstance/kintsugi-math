"""Imperfection metrics — wabi-sabi for your data.

Wabi-sabi is the Japanese aesthetic of imperfection.  This module
measures the *beauty* of errors and partial data: how much entropy
is in the error distribution, how close the recovery ratio is to the
golden ratio, and an overall aesthetic score.

Classes:
    WabiSabiReport — A summary of imperfection metrics.

Functions:
    entropy_of_errors — Shannon entropy of an error distribution.
    golden_ratio      — How close recovered:lost is to φ.
    aesthetic_score   — Overall beauty score for data (0–1).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class WabiSabiReport:
    """A summary of imperfection metrics for a dataset.

    Attributes:
        entropy:       Shannon entropy of the error distribution.
        ratio:         Recovered-to-lost ratio vs golden ratio.
        score:         Overall aesthetic score (0–1).
        imperfections: Number of detected imperfections.
        description:   Human-readable summary.
    """

    entropy: float
    ratio: float
    score: float
    imperfections: int
    description: str = ""

    @property
    def is_beautiful(self) -> bool:
        """True if score >= 0.7 — the imperfections enhance the whole."""
        return self.score >= 0.7

    def __str__(self) -> str:
        bar = "█" * int(self.score * 10) + "░" * (10 - int(self.score * 10))
        return (
            f"WabiSabiReport [{bar}] score={self.score:.3f}\n"
            f"  entropy={self.entropy:.3f}  ratio={self.ratio:.3f}  "
            f"imperfections={self.imperfections}\n"
            f"  {self.description}"
        )


def entropy_of_errors(errors: Sequence[str]) -> float:
    """Compute Shannon entropy of an error type distribution.

    Args:
        errors: Sequence of error type names (e.g. ``["ValueError", "KeyError", ...]``).

    Returns:
        Entropy in bits.  Returns 0.0 for empty input.

    Examples:
        >>> entropy_of_errors(["A", "A", "A"])
        0.0
        >>> entropy_of_errors(["A", "B"])
        1.0
        >>> round(entropy_of_errors(["A", "B", "C", "D"]), 2)
        2.0
    """
    if not errors:
        return 0.0

    counts = Counter(errors)
    total = len(errors)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def golden_ratio(recovered: float, lost: float) -> float:
    """Measure how close recovered:lost is to the golden ratio φ ≈ 1.618.

    Returns a value between 0 and 1, where 1 means perfect golden
    proportion.

    Args:
        recovered: Amount recovered.
        lost:      Amount lost.

    Returns:
        Float between 0 and 1.

    Examples:
        >>> abs(golden_ratio(1.618, 1.0) - 1.0) < 0.01
        True
        >>> golden_ratio(0, 100)
        0.0
    """
    if lost <= 0:
        return 1.0 if recovered > 0 else 0.0

    phi = (1 + math.sqrt(5)) / 2
    ratio = recovered / lost
    distance = abs(ratio - phi)
    return math.exp(-distance)


def aesthetic_score(data: Any) -> float:
    """Compute an aesthetic score for data, where 1.0 is perfect.

    The score is based on completeness, uniformity, and the absence
    of null gaps.  Perfect data (all values present, uniform
    distribution) scores 1.0.  Data with many gaps or extreme
    skew scores lower.

    Args:
        data: Any data — lists, dicts, strings, or numbers.

    Returns:
        Float between 0 and 1.

    Examples:
        >>> aesthetic_score([1, 2, 3, 4, 5])
        1.0
        >>> aesthetic_score([None, None, None])
        0.0
        >>> 0 < aesthetic_score([1, None, 3]) < 1
        True
    """
    if data is None:
        return 0.0

    if isinstance(data, (int, float)):
        return 1.0

    if isinstance(data, str):
        return 1.0 if len(data) > 0 else 0.0

    if isinstance(data, dict):
        if not data:
            return 0.0
        filled = sum(1 for v in data.values() if v is not None)
        return filled / len(data)

    if isinstance(data, (list, tuple, set)):
        items = list(data)
        if not items:
            return 0.0
        filled = sum(1 for item in items if item is not None)
        completeness = filled / len(items)

        # Bonus for uniformity (all distinct)
        distinct = len(set(repr(i) for i in items if i is not None))
        if filled > 0:
            uniformity = min(1.0, distinct / filled)
        else:
            uniformity = 0.0

        return completeness * 0.7 + uniformity * 0.3

    return 0.5
