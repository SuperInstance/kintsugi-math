"""Broken data reassembly — collect fragments and rejoin with gold.

When operations fail partway through, you're left with partial results.
This module treats those partial results as *fragments* of a broken
whole, and reassembles them with confidence-weighted interpolation
for any gaps.

Classes:
    Fragment           — A piece of partial data with confidence.
    FragmentCollection — An ordered group of fragments.

Functions:
    collect_fragments  — Gather partial results into a collection.
    sort_by_priority   — Sort fragments by confidence (descending).
    reassemble         — Merge fragments into complete data with interpolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Fragment:
    """A piece of partial data with an associated confidence score.

    Attributes:
        data:       The partial data payload.
        confidence: How trustworthy this fragment is (0.0–1.0).
        source:     Optional label for where this fragment came from.
        index:      Optional position hint for reassembly ordering.
    """

    data: Any
    confidence: float = 1.0
    source: str = ""
    index: int | None = None

    @property
    def is_reliable(self) -> bool:
        """True if confidence >= 0.5."""
        return self.confidence >= 0.5

    def __str__(self) -> str:
        src = f" from {self.source}" if self.source else ""
        return f"Fragment(confidence={self.confidence:.2f}{src}, data={self.data!r})"


@dataclass
class FragmentCollection:
    """An ordered group of fragments awaiting reassembly.

    Attributes:
        fragments: The collected fragments.
    """

    fragments: list[Fragment] = field(default_factory=list)

    def add(self, fragment: Fragment) -> None:
        """Add a fragment to the collection."""
        self.fragments.append(fragment)

    @property
    def total_confidence(self) -> float:
        """Sum of all fragment confidences."""
        return sum(f.confidence for f in self.fragments)

    @property
    def average_confidence(self) -> float:
        """Mean confidence across fragments."""
        return self.total_confidence / max(len(self.fragments), 1)

    @property
    def reliable_count(self) -> int:
        """Number of fragments with confidence >= 0.5."""
        return sum(1 for f in self.fragments if f.is_reliable)

    def __len__(self) -> int:
        return len(self.fragments)

    def __iter__(self):
        return iter(self.fragments)

    def __getitem__(self, index: int) -> Fragment:
        return self.fragments[index]


def collect_fragments(partial_results: list[dict[str, Any]]) -> FragmentCollection:
    """Gather partial results into a FragmentCollection.

    Each dict should have ``"data"`` and optionally ``"confidence"``,
    ``"source"``, and ``"index"`` keys.

    Args:
        partial_results: List of dicts describing partial data.

    Returns:
        A FragmentCollection ready for reassembly.

    Examples:
        >>> coll = collect_fragments([
        ...     {"data": "hello", "confidence": 0.9, "source": "cache"},
        ...     {"data": "world", "confidence": 0.7, "source": "network"},
        ... ])
        >>> len(coll)
        2
        >>> coll[0].data
        'hello'
    """
    collection = FragmentCollection()
    for item in partial_results:
        collection.add(Fragment(
            data=item.get("data"),
            confidence=item.get("confidence", 0.5),
            source=item.get("source", ""),
            index=item.get("index"),
        ))
    return collection


def sort_by_priority(fragments: FragmentCollection | list[Fragment]) -> list[Fragment]:
    """Sort fragments by confidence, highest first.

    Args:
        fragments: A FragmentCollection or plain list of Fragments.

    Returns:
        Sorted list of Fragments.

    Examples:
        >>> frags = [Fragment("b", 0.3), Fragment("a", 0.9), Fragment("c", 0.6)]
        >>> [f.data for f in sort_by_priority(frags)]
        ['a', 'c', 'b']
    """
    if isinstance(fragments, FragmentCollection):
        frags = fragments.fragments
    else:
        frags = list(fragments)
    return sorted(frags, key=lambda f: f.confidence, reverse=True)


def reassemble(
    fragments: FragmentCollection | list[Fragment],
    gap_filler: Callable[[int, int], Any] | None = None,
) -> list[Any]:
    """Reassemble fragments into complete data with gap interpolation.

    Fragments are sorted by their ``index`` (if set) or by their
    position in the list.  Gaps in the index sequence are filled
    using the ``gap_filler`` callback, which receives the gap position
    and total expected length.

    Args:
    fragments: The fragments to reassemble.
        gap_filler: Optional callable(gap_position, total_length) -> Any.
            Defaults to ``None`` (gaps become ``None``).

    Returns:
        List of reassembled data items with gaps filled.

    Examples:
        >>> frags = [
        ...     Fragment("a", 0.9, index=0),
        ...     Fragment("c", 0.8, index=2),
        ... ]
        >>> reassemble(frags, gap_filler=lambda pos, total: f"gap-{pos}")
        ['a', 'gap-1', 'c']
        >>> reassemble(frags)
        ['a', None, 'c']
    """
    if isinstance(fragments, FragmentCollection):
        frags = list(fragments.fragments)
    else:
        frags = list(fragments)

    if not frags:
        return []

    # Assign sequential indices to fragments without them
    for i, f in enumerate(frags):
        if f.index is None:
            f.index = i

    # Sort by index
    frags.sort(key=lambda f: f.index)  # type: ignore[arg-type]

    # Determine total span
    max_idx = max(f.index for f in frags)  # type: ignore[arg-type]
    result: list[Any] = [None] * (max_idx + 1)

    # Place fragments
    for f in frags:
        result[f.index] = f.data  # type: ignore[index]

    # Fill gaps
    for i in range(len(result)):
        if result[i] is None and gap_filler is not None:
            result[i] = gap_filler(i, len(result))

    return result
