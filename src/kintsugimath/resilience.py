"""Fault injection testing — deliberate cracks to test the gold.

Resilience is measured by how beautifully a system recovers from
faults.  This module provides tools to inject faults into functions,
measure recovery rates, and produce aesthetic quality scores for
the recovery process.

Classes:
    ResilienceReport — Summary of a system's fault recovery performance.

Functions:
    inject_faults    — Run a function with random fault injection.
    measure_recovery — Test a system's resilience to a series of faults.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ResilienceReport:
    """Summary of a system's fault recovery performance.

    Attributes:
        recovery_rate:       Fraction of faults that were recovered (0–1).
        mean_time_to_repair: Average seconds to recover from a fault.
        aesthetic_quality:   How beautiful the recovery was (0–1).
        total_faults:        Number of faults injected.
        successful_recoveries: Number of faults recovered.
        details:             Per-fault details.
    """

    recovery_rate: float
    mean_time_to_repair: float
    aesthetic_quality: float
    total_faults: int
    successful_recoveries: int
    details: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_resilient(self) -> bool:
        """True if recovery_rate >= 0.8 and aesthetic_quality >= 0.6."""
        return self.recovery_rate >= 0.8 and self.aesthetic_quality >= 0.6

    def __str__(self) -> str:
        return (
            f"ResilienceReport: {self.successful_recoveries}/{self.total_faults} "
            f"recovered ({self.recovery_rate:.1%}), "
            f"MTTR={self.mean_time_to_repair:.3f}s, "
            f"aesthetic={self.aesthetic_quality:.3f}"
        )


def inject_faults(
    fn: Callable[..., Any],
    fault_rate: float = 0.1,
    iterations: int = 100,
    fault_factory: Callable[[], Exception] | None = None,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run *fn* multiple times, randomly injecting faults.

    Each iteration either runs the function normally or raises a fault
    (controlled by ``fault_rate``).  Results are collected for analysis.

    Args:
        fn:            The function to test.
        fault_rate:    Probability of injecting a fault per iteration (0–1).
        iterations:    Number of iterations to run.
        fault_factory: Optional callable producing exceptions to inject.
        args:          Positional arguments to pass to *fn*.
        kwargs:        Keyword arguments to pass to *fn*.

    Returns:
        Dict with keys ``"successes"``, ``"faults"``, ``"results"``,
        ``"fault_rate"``.

    Examples:
        >>> result = inject_faults(lambda x: x * 2, fault_rate=0.5,
        ...                        iterations=20, args=(5,))
        >>> result["successes"] + result["faults"] == 20
        True
    """
    if kwargs is None:
        kwargs = {}

    successes = 0
    faults = 0
    results: list[Any] = []

    default_fault = RuntimeError("Injected fault")

    for _ in range(iterations):
        if random.random() < fault_rate:
            faults += 1
            exc = fault_factory() if fault_factory else default_fault
            results.append({"status": "fault", "exception": exc})
        else:
            try:
                value = fn(*args, **kwargs)
                successes += 1
                results.append({"status": "success", "value": value})
            except Exception as exc:
                faults += 1
                results.append({"status": "error", "exception": exc})

    return {
        "successes": successes,
        "faults": faults,
        "results": results,
        "fault_rate": fault_rate,
    }


def measure_recovery(
    system: Callable[[Exception], bool],
    faults: list[Exception],
) -> ResilienceReport:
    """Test a system's resilience by feeding it faults and measuring recovery.

    The *system* callable receives an exception and returns ``True`` if
    it successfully recovered, ``False`` otherwise.  Recovery time is
    measured for each fault.

    Args:
        system: A callable(exception) -> bool returning True on recovery.
        faults: List of exceptions to throw at the system.

    Returns:
        A ResilienceReport with recovery statistics.

    Examples:
        >>> resilient = lambda e: isinstance(e, ValueError)
        >>> report = measure_recovery(resilient, [
        ...     ValueError("a"), TypeError("b"), ValueError("c"),
        ... ])
        >>> report.recovery_rate
        0.666...
        >>> report.total_faults
        3
    """
    details: list[dict[str, Any]] = []
    successful = 0
    total_time = 0.0

    for fault in faults:
        start = time.perf_counter()
        try:
            recovered = system(fault)
        except Exception:
            recovered = False
        elapsed = time.perf_counter() - start

        if recovered:
            successful += 1
            total_time += elapsed

        details.append({
            "fault": fault,
            "recovered": recovered,
            "time": elapsed,
        })

    recovery_rate = successful / max(len(faults), 1)
    mttr = total_time / max(successful, 1)

    # Aesthetic quality: blend of recovery rate and speed
    # Fast + high recovery = more beautiful
    speed_score = max(0.0, 1.0 - mttr * 10)  # degrade if > 0.1s
    aesthetic_quality = recovery_rate * 0.7 + speed_score * 0.3

    return ResilienceReport(
        recovery_rate=recovery_rate,
        mean_time_to_repair=mttr,
        aesthetic_quality=aesthetic_quality,
        total_faults=len(faults),
        successful_recoveries=successful,
        details=details,
    )
