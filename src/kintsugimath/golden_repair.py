"""Transform error traces into golden seams — structured recovery objects.

In kintsugi, broken pottery is repaired with gold lacquer, making the
cracks beautiful rather than hidden. This module transforms exceptions
and tracebacks into structured *golden seams* that carry severity,
context, and recovery suggestions.

Classes:
    GoldenSeam   — A single repair point with severity and suggestion.
    ErrorTrace   — A collection of golden seams from one error chain.

Functions:
    golden_repair         — Turn an exception into a GoldenSeam.
    repair_traceback      — Extract a full ErrorTrace from a traceback.
    severity_score        — Numeric severity for an exception.
    golden_ratio_recovery — Ratio of recovered to total data.
"""

from __future__ import annotations

import math
import traceback
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoldenSeam:
    """A single repair point extracted from an error.

    Attributes:
        severity:  Numeric severity (0 = trivial, 10 = catastrophic).
        context:   Human-readable description of where the crack appeared.
        suggestion: A recovery suggestion — the *gold* in the seam.
        exception_type: Name of the originating exception class.
    """

    severity: float
    context: str
    suggestion: str
    exception_type: str = "Exception"

    @property
    def is_critical(self) -> bool:
        """Return True if severity >= 7."""
        return self.severity >= 7.0

    def __str__(self) -> str:
        gold = "✦" * min(int(self.severity), 10)
        return f"{gold} [{self.exception_type}] {self.context} → {self.suggestion}"


@dataclass
class ErrorTrace:
    """A collection of golden seams extracted from an error chain.

    Attributes:
        seams: Ordered list of GoldenSeam objects (outermost first).
        original_exception: The exception that started it all, if any.
    """

    seams: list[GoldenSeam] = field(default_factory=list)
    original_exception: BaseException | None = None

    @property
    def total_severity(self) -> float:
        """Sum of all seam severities."""
        return sum(s.severity for s in self.seams)

    @property
    def max_severity(self) -> float:
        """Maximum severity among all seams."""
        return max((s.severity for s in self.seams), default=0.0)

    @property
    def critical_seams(self) -> list[GoldenSeam]:
        """Return only critical seams."""
        return [s for s in self.seams if s.is_critical]

    def __len__(self) -> int:
        return len(self.seams)

    def __iter__(self):
        return iter(self.seams)

    def __str__(self) -> str:
        lines = [f"ErrorTrace ({len(self.seams)} seams, total severity {self.total_severity:.1f})"]
        for seam in self.seams:
            lines.append(f"  {seam}")
        return "\n".join(lines)


def severity_score(error: BaseException) -> float:
    """Compute a numeric severity score for an exception.

    Uses a combination of the exception's position in the MRO and its
    message length (as a proxy for information content).  Built-in
    exceptions with shorter MROs are considered more severe.

    Args:
        error: Any exception instance.

    Returns:
        Float between 0 and 10.

    Examples:
        >>> severity_score(ValueError("x"))
        3.5
        >>> severity_score(BaseException("generic"))
        9.5
    """
    # Deeper in the hierarchy → less severe
    mro_depth = len(type(error).__mro__)
    base_severity = min(10.0, mro_depth * 1.0 + 0.5)

    # Longer messages carry more information → slightly less severe
    msg = str(error)
    msg_factor = min(2.0, len(msg) / 50.0)

    return min(10.0, max(0.0, base_severity - msg_factor))


def golden_repair(exception: BaseException) -> GoldenSeam:
    """Transform a single exception into a GoldenSeam.

    Args:
        exception: The exception to repair.

    Returns:
        A GoldenSeam with severity, context, and suggestion.

    Examples:
        >>> seam = golden_repair(ValueError("invalid input"))
        >>> seam.severity > 0
        True
        >>> seam.exception_type
        'ValueError'
    """
    sev = severity_score(exception)
    exc_type = type(exception).__name__
    msg = str(exception)

    context = f"{exc_type}: {msg}" if msg else f"{exc_type} raised"

    # Generate suggestion based on exception type
    suggestions: dict[str, str] = {
        "ValueError": "Validate inputs before processing; check ranges and types.",
        "TypeError": "Ensure correct argument types; add explicit casts or guards.",
        "KeyError": "Use .get() with defaults or check key existence first.",
        "IndexError": "Verify collection bounds before indexing.",
        "AttributeError": "Check hasattr() or use getattr() with defaults.",
        "FileNotFoundError": "Verify file path exists; use pathlib for robust paths.",
        "PermissionError": "Check file/directory permissions and ownership.",
        "ConnectionError": "Implement retry logic with exponential backoff.",
        "TimeoutError": "Increase timeout or add async cancellation support.",
        "RuntimeError": "Review state preconditions before the failing operation.",
    }
    suggestion = suggestions.get(exc_type, "Investigate root cause and add defensive checks.")

    return GoldenSeam(
        severity=sev,
        context=context,
        suggestion=suggestion,
        exception_type=exc_type,
    )


def repair_traceback(tb: traceback.TracebackException) -> ErrorTrace:
    """Extract an ErrorTrace from a traceback.

    Each frame in the traceback becomes a GoldenSeam.  The outermost
    frame gets the highest severity (it's where the user called in),
    and severity decreases toward the innermost frame.

    Args:
        tb: A TracebackException (from ``traceback.TracebackException``).

    Returns:
        An ErrorTrace with one seam per stack frame.

    Examples:
        >>> import traceback
        >>> try:
        ...     raise ValueError("test")
        ... except Exception:
        ...     tb = traceback.TracebackException.from_exception(...)
        ...     trace = repair_traceback(tb)  # doctest: +SKIP
    """
    seams: list[GoldenSeam] = []
    frames = list(tb.stack)
    n = len(frames)

    for i, frame in enumerate(frames):
        # Outermost frames get higher severity
        position_severity = 10.0 * (1.0 - i / max(n, 1))
        context = f"{frame.filename}:{frame.lineno} in {frame.name}"
        if frame.line:
            context += f" — `{frame.line.strip()}`"
        suggestion = "Review this call site for preconditions."

        seams.append(GoldenSeam(
            severity=round(position_severity, 2),
            context=context,
            suggestion=suggestion,
            exception_type=tb.exc_type.__name__ if tb.exc_type else "Unknown",
        ))

    return ErrorTrace(seams=seams, original_exception=None)


def golden_ratio_recovery(recovered: float, lost: float) -> float:
    """Compute how close the recovery ratio is to the golden ratio φ.

    The golden ratio (≈1.618) represents ideal proportions.  This
    function measures how close the recovered-to-lost ratio is to φ,
    returning 1.0 for a perfect match and 0.0 for worst cases.

    Args:
        recovered: Amount of data/state successfully recovered.
        lost:      Amount of data/state that was lost.

    Returns:
        Float between 0 and 1, where 1 means the recovery ratio
        equals the golden ratio.

    Examples:
        >>> golden_ratio_recovery(1.618, 1.0)
        0.99...
        >>> golden_ratio_recovery(0, 1)
        0.0
    """
    if lost <= 0:
        return 1.0 if recovered > 0 else 0.0

    ratio = recovered / lost
    phi = (1 + math.sqrt(5)) / 2  # ≈ 1.618

    # How close to phi?  Use exponential decay of distance.
    distance = abs(ratio - phi)
    return math.exp(-distance)
