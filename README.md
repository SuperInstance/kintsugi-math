# kintsugi-math

> The mathematics of beautiful error recovery — fault tolerance as an aesthetic principle.

*Kintsugi* (金継ぎ) is the Japanese art of repairing broken pottery with gold. This package implements the **mathematics** of beautiful error recovery: transforming errors into structured recovery objects, reassembling fragmented data, measuring imperfection, and mapping error propagation.

## Installation

```bash
pip install kintsugi-math
```

## Modules

- **golden_repair** — Transform error traces into golden seams (structured recovery objects)
- **fragments** — Broken data reassembly with confidence-weighted interpolation
- **wabi_sabi** — Imperfection metrics (entropy, golden ratio, aesthetic scores)
- **resilience** — Fault injection testing and recovery measurement
- **cracks** — Error propagation graphs and golden joint identification

## Quick Start

```python
from kintsugimath import golden_repair, GoldenSeam

# Transform an error into a golden seam
seam = golden_repair(ValueError("invalid input"))
print(seam)  # ✦✦✦ [ValueError] ValueError: invalid input → Validate inputs...

# Reassemble fragmented data
from kintsugimath import collect_fragments, reassemble
coll = collect_fragments([
    {"data": "hello", "confidence": 0.9, "index": 0},
    {"data": "world", "confidence": 0.7, "index": 2},
])
result = reassemble(coll, gap_filler=lambda pos, _: f"<gap-{pos}>")
# ['hello', '<gap-1>', 'world']

# Measure imperfection
from kintsugimath import aesthetic_score, entropy_of_errors
score = aesthetic_score([1, 2, None, 4])  # 0.775
entropy = entropy_of_errors(["ValueError", "KeyError", "ValueError"])
```

## License

MIT
