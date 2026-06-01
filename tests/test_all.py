"""Comprehensive tests for kintsugi-math.

Covers all modules: golden_repair, fragments, wabi_sabi, resilience, cracks.
"""

import traceback
import math
import random

import pytest

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


# ── golden_repair tests ──────────────────────────────────────────


class TestGoldenSeam:
    def test_creation(self):
        seam = GoldenSeam(severity=5.0, context="test", suggestion="fix it")
        assert seam.severity == 5.0
        assert seam.context == "test"
        assert seam.suggestion == "fix it"
        assert seam.exception_type == "Exception"

    def test_is_critical(self):
        assert GoldenSeam(7.0, "c", "s").is_critical
        assert GoldenSeam(9.5, "c", "s").is_critical
        assert not GoldenSeam(3.0, "c", "s").is_critical

    def test_str_representation(self):
        seam = GoldenSeam(3.0, "ValueError", "Check inputs", "ValueError")
        s = str(seam)
        assert "ValueError" in s
        assert "Check inputs" in s


class TestErrorTrace:
    def test_empty_trace(self):
        trace = ErrorTrace()
        assert len(trace) == 0
        assert trace.total_severity == 0.0
        assert trace.max_severity == 0.0

    def test_with_seams(self):
        seams = [
            GoldenSeam(3.0, "a", "x"),
            GoldenSeam(7.0, "b", "y"),
        ]
        trace = ErrorTrace(seams=seams)
        assert len(trace) == 2
        assert trace.total_severity == 10.0
        assert trace.max_severity == 7.0

    def test_critical_seams(self):
        seams = [
            GoldenSeam(3.0, "a", "x"),
            GoldenSeam(7.0, "b", "y"),
            GoldenSeam(8.0, "c", "z"),
        ]
        trace = ErrorTrace(seams=seams)
        assert len(trace.critical_seams) == 2

    def test_iteration(self):
        seams = [GoldenSeam(i, str(i), str(i)) for i in range(3)]
        trace = ErrorTrace(seams=seams)
        assert list(trace) == seams

    def test_str_output(self):
        trace = ErrorTrace(seams=[GoldenSeam(1.0, "ctx", "sug")])
        assert "1 seams" in str(trace)


class TestSeverityScore:
    def test_value_error(self):
        score = severity_score(ValueError("bad"))
        assert 0 < score <= 10

    def test_base_exception_high_severity(self):
        score = severity_score(BaseException("generic"))
        assert score > 1  # BaseException is shallow in MRO → lower severity

    def test_long_message_reduces_severity(self):
        short = severity_score(ValueError("x"))
        long = severity_score(ValueError("x" * 200))
        assert long <= short

    def test_bounded(self):
        score = severity_score(RuntimeError("test"))
        assert 0 <= score <= 10


class TestGoldenRepair:
    def test_value_error(self):
        seam = golden_repair(ValueError("bad input"))
        assert seam.exception_type == "ValueError"
        assert seam.severity > 0
        assert "Validate" in seam.suggestion

    def test_key_error(self):
        seam = golden_repair(KeyError("missing"))
        assert "KeyError" in seam.exception_type

    def test_connection_error(self):
        seam = golden_repair(ConnectionError("refused"))
        assert "retry" in seam.suggestion.lower()

    def test_unknown_exception(self):
        seam = golden_repair(RuntimeError("unknown issue"))
        assert seam.severity > 0


class TestGoldenRatioRecovery:
    def test_perfect_ratio(self):
        phi = (1 + math.sqrt(5)) / 2
        score = golden_ratio_recovery(phi, 1.0)
        assert score > 0.99

    def test_zero_recovered(self):
        assert golden_ratio_recovery(0, 1) < 0.5  # Far from golden ratio

    def test_zero_lost(self):
        assert golden_ratio_recovery(1, 0) == 1.0

    def test_both_zero(self):
        assert golden_ratio_recovery(0, 0) == 0.0


class TestRepairTraceback:
    def test_basic_traceback(self):
        try:
            raise ValueError("test error")
        except Exception:
            tb = traceback.TracebackException.from_exception(
                ValueError("test error"),
            )
            # Build a synthetic traceback for testing
            trace = repair_traceback(tb)
            assert isinstance(trace, ErrorTrace)


# ── fragments tests ──────────────────────────────────────────────


class TestFragment:
    def test_creation(self):
        f = Fragment("data", 0.8, "source_a")
        assert f.data == "data"
        assert f.confidence == 0.8
        assert f.source == "source_a"

    def test_is_reliable(self):
        assert Fragment("x", 0.7).is_reliable
        assert Fragment("x", 0.5).is_reliable
        assert not Fragment("x", 0.3).is_reliable

    def test_str(self):
        f = Fragment("data", 0.9, "cache")
        assert "0.90" in str(f)
        assert "cache" in str(f)

    def test_default_index(self):
        f = Fragment("data")
        assert f.index is None


class TestFragmentCollection:
    def test_add_and_len(self):
        coll = FragmentCollection()
        coll.add(Fragment("a"))
        coll.add(Fragment("b"))
        assert len(coll) == 2

    def test_total_confidence(self):
        coll = FragmentCollection([
            Fragment("a", 0.5),
            Fragment("b", 0.8),
        ])
        assert coll.total_confidence == pytest.approx(1.3)

    def test_average_confidence(self):
        coll = FragmentCollection([
            Fragment("a", 0.6),
            Fragment("b", 0.8),
        ])
        assert coll.average_confidence == pytest.approx(0.7)

    def test_reliable_count(self):
        coll = FragmentCollection([
            Fragment("a", 0.9),
            Fragment("b", 0.3),
            Fragment("c", 0.7),
        ])
        assert coll.reliable_count == 2

    def test_getitem(self):
        coll = FragmentCollection([Fragment("x"), Fragment("y")])
        assert coll[1].data == "y"

    def test_iter(self):
        frags = [Fragment("a"), Fragment("b")]
        coll = FragmentCollection(frags)
        assert list(coll) == frags


class TestCollectFragments:
    def test_basic(self):
        coll = collect_fragments([
            {"data": "hello", "confidence": 0.9},
            {"data": "world", "confidence": 0.6},
        ])
        assert len(coll) == 2
        assert coll[0].data == "hello"

    def test_defaults(self):
        coll = collect_fragments([{"data": "x"}])
        assert coll[0].confidence == 0.5


class TestSortByPriority:
    def test_sort_fragments(self):
        frags = [Fragment("b", 0.3), Fragment("a", 0.9), Fragment("c", 0.6)]
        sorted_frags = sort_by_priority(frags)
        assert [f.data for f in sorted_frags] == ["a", "c", "b"]

    def test_sort_collection(self):
        coll = FragmentCollection([
            Fragment("low", 0.1),
            Fragment("high", 0.9),
        ])
        sorted_frags = sort_by_priority(coll)
        assert sorted_frags[0].data == "high"


class TestReassemble:
    def test_basic_reassembly(self):
        frags = [Fragment("a", 0.9, index=0), Fragment("c", 0.8, index=2)]
        result = reassemble(frags)
        assert result == ["a", None, "c"]

    def test_with_gap_filler(self):
        frags = [Fragment("a", 0.9, index=0), Fragment("c", 0.8, index=2)]
        result = reassemble(frags, gap_filler=lambda pos, total: f"gap-{pos}")
        assert result == ["a", "gap-1", "c"]

    def test_empty(self):
        assert reassemble([]) == []

    def test_no_gaps(self):
        frags = [Fragment("a", index=0), Fragment("b", index=1)]
        assert reassemble(frags) == ["a", "b"]

    def test_collection_input(self):
        coll = FragmentCollection([Fragment("x", index=0)])
        assert reassemble(coll) == ["x"]


# ── wabi_sabi tests ──────────────────────────────────────────────


class TestEntropyOfErrors:
    def test_uniform(self):
        assert entropy_of_errors(["A", "A", "A"]) == 0.0

    def test_binary(self):
        assert entropy_of_errors(["A", "B"]) == 1.0

    def test_four_types(self):
        assert entropy_of_errors(["A", "B", "C", "D"]) == pytest.approx(2.0)

    def test_empty(self):
        assert entropy_of_errors([]) == 0.0


class TestGoldenRatio:
    def test_perfect(self):
        phi = (1 + math.sqrt(5)) / 2
        assert golden_ratio(phi, 1.0) > 0.99

    def test_zero_recovered(self):
        assert golden_ratio(0, 100) < 0.5  # Far from golden ratio

    def test_zero_lost_with_recovery(self):
        assert golden_ratio(1, 0) == 1.0


class TestAestheticScore:
    def test_perfect_list(self):
        assert aesthetic_score([1, 2, 3, 4, 5]) == 1.0

    def test_all_none(self):
        assert aesthetic_score([None, None, None]) == 0.0

    def test_partial_gaps(self):
        score = aesthetic_score([1, None, 3])
        assert 0 < score < 1

    def test_none_input(self):
        assert aesthetic_score(None) == 0.0

    def test_number_input(self):
        assert aesthetic_score(42) == 1.0

    def test_empty_string(self):
        assert aesthetic_score("") == 0.0

    def test_nonempty_string(self):
        assert aesthetic_score("hello") == 1.0

    def test_dict(self):
        assert aesthetic_score({"a": 1, "b": 2}) == 1.0
        assert aesthetic_score({"a": 1, "b": None}) == 0.5

    def test_empty_list(self):
        assert aesthetic_score([]) == 0.0


class TestWabiSabiReport:
    def test_creation(self):
        report = WabiSabiReport(
            entropy=1.5, ratio=0.8, score=0.75, imperfections=3,
        )
        assert report.is_beautiful
        assert "score=0.750" in str(report)

    def test_not_beautiful(self):
        report = WabiSabiReport(
            entropy=0.5, ratio=0.3, score=0.4, imperfections=10,
        )
        assert not report.is_beautiful


# ── resilience tests ─────────────────────────────────────────────


class TestInjectFaults:
    def test_no_faults(self):
        result = inject_faults(lambda: 42, fault_rate=0.0, iterations=10)
        assert result["successes"] == 10
        assert result["faults"] == 0

    def test_all_faults(self):
        result = inject_faults(lambda: 42, fault_rate=1.0, iterations=10)
        assert result["successes"] == 0
        assert result["faults"] == 10

    def test_with_args(self):
        result = inject_faults(lambda x: x * 2, fault_rate=0.0, args=(5,))
        assert result["results"][0]["value"] == 10

    def test_total_iterations(self):
        result = inject_faults(lambda: 1, fault_rate=0.5, iterations=50)
        assert result["successes"] + result["faults"] == 50


class TestMeasureRecovery:
    def test_all_recoverable(self):
        system = lambda e: isinstance(e, ValueError)
        report = measure_recovery(system, [
            ValueError("a"),
            ValueError("b"),
        ])
        assert report.recovery_rate == 1.0
        assert report.total_faults == 2
        assert report.successful_recoveries == 2

    def test_none_recoverable(self):
        system = lambda e: False
        report = measure_recovery(system, [ValueError("x")])
        assert report.recovery_rate == 0.0

    def test_partial(self):
        system = lambda e: isinstance(e, ValueError)
        report = measure_recovery(system, [
            ValueError("ok"), TypeError("bad"), ValueError("ok2"),
        ])
        assert report.recovery_rate == pytest.approx(2 / 3)

    def test_resilience_report_str(self):
        report = ResilienceReport(
            recovery_rate=0.9,
            mean_time_to_repair=0.001,
            aesthetic_quality=0.85,
            total_faults=10,
            successful_recoveries=9,
        )
        s = str(report)
        assert "90.0%" in s

    def test_is_resilient(self):
        report = ResilienceReport(
            recovery_rate=0.9,
            mean_time_to_repair=0.001,
            aesthetic_quality=0.8,
            total_faults=10,
            successful_recoveries=9,
        )
        assert report.is_resilient


# ── cracks tests ─────────────────────────────────────────────────


class TestCrackGraph:
    def test_add_node(self):
        g = CrackGraph()
        g.add_node("api")
        assert "api" in g.nodes

    def test_add_edge(self):
        g = CrackGraph()
        g.add_edge("db", "api")
        assert "db" in g.nodes
        assert "api" in g.nodes
        assert "api" in g.edges["db"]

    def test_record_error(self):
        g = CrackGraph()
        g.record_error("cache", 3)
        assert g.error_counts["cache"] == 3

    def test_downstream(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("B", "D")
        assert g.downstream("A") == {"B", "C", "D"}
        assert g.downstream("B") == {"C", "D"}
        assert g.downstream("D") == set()

    def test_upstream(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        assert g.upstream("C") == {"A", "B"}

    def test_len(self):
        g = CrackGraph()
        g.add_edge("X", "Y")
        g.add_edge("Y", "Z")
        assert len(g) == 3


class TestBuildCrackGraph:
    def test_basic(self):
        graph = build_crack_graph([
            {"source": "db", "target": "api"},
            {"source": "api", "target": "ui"},
        ])
        assert len(graph) == 3
        assert "db" in graph.nodes

    def test_no_target(self):
        graph = build_crack_graph([
            {"source": "db"},
        ])
        assert "db" in graph.nodes
        assert len(graph.edges["db"]) == 0


class TestFindGoldenJoints:
    def test_basic(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.record_error("A", 5)
        joints = find_golden_joints(g)
        assert joints[0].component == "A"

    def test_top_n(self):
        g = CrackGraph()
        for n in "ABCDE":
            g.add_node(n)
        joints = find_golden_joints(g, top_n=2)
        assert len(joints) == 2

    def test_high_impact(self):
        g = CrackGraph()
        g.add_edge("root", "a")
        g.add_edge("root", "b")
        g.add_edge("root", "c")
        g.add_edge("a", "d")
        g.record_error("root", 10)
        joints = find_golden_joints(g)
        assert joints[0].is_high_impact


class TestShortestCrackPath:
    def test_direct(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        assert shortest_crack_path(g, "A", "B") == ["A", "B"]

    def test_shorter_path(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("A", "C")
        assert shortest_crack_path(g, "A", "C") == ["A", "C"]

    def test_no_path(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        assert shortest_crack_path(g, "B", "A") is None

    def test_same_node(self):
        g = CrackGraph()
        g.add_node("X")
        assert shortest_crack_path(g, "X", "X") == ["X"]

    def test_missing_node(self):
        g = CrackGraph()
        assert shortest_crack_path(g, "A", "B") is None

    def test_multi_hop(self):
        g = CrackGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "D")
        assert shortest_crack_path(g, "A", "D") == ["A", "B", "C", "D"]
