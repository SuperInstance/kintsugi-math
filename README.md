# kintsugi-math

> The mathematics of beautiful error recovery — inspired by the Japanese art of repairing pottery with gold.

## What This Does

`kintsugi-math` treats software failures the way a kintsugi artisan treats broken pottery: not as something to hide, but as something to make beautiful. It transforms exceptions into structured recovery objects ("golden seams"), reassembles fragmented partial data, measures crack propagation in dependency graphs, and quantifies how aesthetically pleasing your error recovery actually is.

Use it when you want your systems to fail gracefully, when you need to reassemble partial results from interrupted operations, or when you want to measure and improve resilience.

## The Cultural Root

Kintsugi (金継ぎ, "golden joinery") is the Japanese art of repairing broken pottery with lacquer dusted with powdered gold. The philosophy: breakage and repair are part of the history of an object, not something to disguise. The mathematical insight is that **error recovery has an aesthetic dimension** — a system that recovers 80% of its data with a clean interface is more "beautiful" than one that recovers 90% but leaves a mess. This maps directly to graceful degradation in distributed systems.

## Install

```bash
pip install kintsugi-math
```

## Quick Start

```python
from kintsugimath import golden_repair, severity_score
from kintsugimath.fragments import Fragment, FragmentCollection, reassemble
from kintsugimath.wabi_sabi import aesthetic_score, entropy_of_errors
from kintsugimath.cracks import CrackGraph
from kintsugimath.resilience import inject_faults, measure_recovery

# Transform an exception into a golden seam
try:
    result = risky_operation()
except Exception as e:
    seam = golden_repair(e)
    print(seam)
    # ✦✦✦✦ [ValueError] ValueError: invalid input → Validate inputs before processing; check ranges and types.
    print(f"Severity: {seam.severity}, Critical: {seam.is_critical}")

# Reassemble fragmented data
fragments = FragmentCollection()
fragments.add(Fragment(data=[1.0, 2.0], confidence=0.9, index=0))
fragments.add(Fragment(data=[3.0, 4.0], confidence=0.7, index=1))
fragments.add(Fragment(data=[5.0], confidence=0.3, index=2))
result = reassemble(fragments, target_length=5)
# [1.0, 2.0, 3.0, 4.0, 5.0] — gaps filled by interpolation

# Measure aesthetic quality of your data
score = aesthetic_score([1, 2, 3, None, 5])  # 0.7

# Model crack propagation in a dependency graph
graph = CrackGraph()
graph.add_crack("database", "api_gateway", weight=0.8)
graph.add_crack("api_gateway", "frontend", weight=0.6)
resilience = graph.measure_resilience()

# Inject faults to test recovery
def my_func():
    return 42

report = inject_faults(my_func, fault_rate=0.3, iterations=100)
print(f"Recovery rate: {report['fault_rate']:.1%}")
```

## API Reference

### `golden_repair` module

#### `GoldenSeam`
```python
@dataclass
class GoldenSeam:
    severity: float       # 0-10, how bad
    context: str          # Where the crack appeared
    suggestion: str       # How to fix it (the "gold")
    exception_type: str   # Exception class name

    @property
    def is_critical(self) -> bool  # severity >= 7
```

#### `ErrorTrace`
```python
@dataclass
class ErrorTrace:
    seams: list[GoldenSeam]
    original_exception: BaseException | None

    @property
    def total_severity(self) -> float
    @property
    def max_severity(self) -> float
    @property
    def critical_seams(self) -> list[GoldenSeam]
```

#### `golden_repair(exception) → GoldenSeam`
Transform any exception into a structured recovery object with severity, context, and actionable suggestions.

#### `repair_traceback(tb) → ErrorTrace`
Convert a `traceback.TracebackException` into an ordered list of golden seams, one per stack frame. Outer frames get higher severity.

#### `severity_score(error) → float`
Compute 0–10 severity from exception MRO depth and message length.

#### `golden_ratio_recovery(recovered, lost) → float`
How close is your recovered:lost ratio to φ ≈ 1.618? Returns 0–1 where 1 = perfect golden proportion.

### `fragments` module

#### `Fragment`
```python
@dataclass
class Fragment:
    data: Any
    confidence: float = 1.0   # 0–1 trustworthiness
    source: str = ""
    index: int | None = None
```

#### `FragmentCollection`
Collect and manage fragments. Methods: `add()`, `sorted()`, `size`.

#### `reassemble(collection, target_length) → list`
Merge fragments into complete data. High-confidence fragments are placed first; gaps are filled by linear interpolation.

#### `collect_fragments(partial_results) → FragmentCollection`
Gather partial results into a fragment collection.

### `wabi_sabi` module

#### `WabiSabiReport`
```python
@dataclass
class WabiSabiReport:
    entropy: float
    ratio: float
    score: float
    imperfections: int
    description: str
```

#### `entropy_of_errors(errors) → float`
Shannon entropy of an error distribution. Uniform distributions → high entropy (beautiful). All same → 0 entropy.

#### `golden_ratio(recovered, lost) → float`
Measure how close the recovery ratio is to φ.

#### `aesthetic_score(data) → float`
Overall beauty score 0–1. Based on completeness, uniformity, and absence of nulls.

### `cracks` module

#### `CrackGraph`
Directed graph of error propagation between system components.

- `add_crack(source, target, weight)` — Add a failure edge
- `propagate_from(node)` — Trace failure cascade
- `measure_resilience()` — Overall resilience score

### `resilience` module

#### `ResilienceReport`
```python
@dataclass
class ResilienceReport:
    recovery_rate: float
    mean_time_to_repair: float
    aesthetic_quality: float
    total_faults: int
    successful_recoveries: int
```

#### `inject_faults(fn, fault_rate, iterations, ...) → dict`
Run a function repeatedly with random fault injection. Returns success/fault statistics.

#### `measure_recovery(fn, faults, ...) → ResilienceReport`
Test a function against a series of specific faults and measure recovery.

## How It Works

**Golden Seams** extract structured metadata from Python exceptions. Each exception type gets a domain-specific recovery suggestion. Severity is computed from the MRO depth — more specific exceptions (deeper in the hierarchy) are considered less catastrophic.

**Fragment Reassembly** treats partial results like pottery shards. Each fragment carries a confidence score. The reassembly algorithm sorts by confidence, places high-trust fragments at their indicated positions, and fills gaps with linear interpolation weighted by neighboring confidences.

**Wabi-Sabi Metrics** use Shannon entropy to measure error diversity (diverse errors = healthy system discovering edge cases) and the golden ratio to evaluate recovery proportions. The aesthetic score combines completeness (no nulls), uniformity (diverse values), and recovery quality.

**Crack Propagation** models failures as a directed weighted graph. Resilience is measured by how many nodes survive when a crack propagates from any source, weighted by edge importance.

## The Math

**Shannon Entropy:** H(X) = −Σ p(x) log₂ p(x), where p(x) is the frequency of error type x.

**Golden Ratio:** φ = (1 + √5) / 2 ≈ 1.618. Recovery quality = exp(−|recovered/lost − φ|).

**Severity Scoring:** severity = min(10, MRO_depth × 1.0 + 0.5 − msg_length/50).

**Linear Interpolation:** For gap [a, b] with confidence weights wₐ, w_b: fill = (wₐ·vₐ + w_b·v_b) / (wₐ + w_b).

## License

MIT
