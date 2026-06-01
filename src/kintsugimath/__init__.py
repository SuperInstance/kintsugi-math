"""kintsugi-math — The mathematics of beautiful error recovery.

Kintsugi is the Japanese art of repairing broken pottery with gold.
This package implements fault tolerance as an aesthetic principle:
transforming errors into structured recovery objects, reassembling
fragmented data, measuring imperfection, and mapping error propagation.

Modules:
    golden_repair — Transform error traces into golden seams.
    fragments     — Broken data reassembly.
    wabi_sabi     — Imperfection metrics.
    resilience    — Fault injection testing.
    cracks        — Error propagation graphs.
"""

from kintsugimath.golden_repair import (
    GoldenSeam,
    ErrorTrace,
    golden_repair,
    repair_traceback,
    severity_score,
    golden_ratio_recovery,
)
from kintsugimath.fragments import (
    Fragment,
    FragmentCollection,
    collect_fragments,
    sort_by_priority,
    reassemble,
)
from kintsugimath.wabi_sabi import (
    entropy_of_errors,
    golden_ratio,
    aesthetic_score,
    WabiSabiReport,
)
from kintsugimath.resilience import (
    inject_faults,
    measure_recovery,
    ResilienceReport,
)
from kintsugimath.cracks import (
    CrackGraph,
    GoldenJoint,
    build_crack_graph,
    find_golden_joints,
    shortest_crack_path,
)

__all__ = [
    # golden_repair
    "GoldenSeam",
    "ErrorTrace",
    "golden_repair",
    "repair_traceback",
    "severity_score",
    "golden_ratio_recovery",
    # fragments
    "Fragment",
    "FragmentCollection",
    "collect_fragments",
    "sort_by_priority",
    "reassemble",
    # wabi_sabi
    "entropy_of_errors",
    "golden_ratio",
    "aesthetic_score",
    "WabiSabiReport",
    # resilience
    "inject_faults",
    "measure_recovery",
    "ResilienceReport",
    # cracks
    "CrackGraph",
    "GoldenJoint",
    "build_crack_graph",
    "find_golden_joints",
    "shortest_crack_path",
]

__version__ = "0.1.0"
