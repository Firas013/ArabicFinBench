"""Tests for canon as the single normalization authority.

The unfairness this prevents: ~20 private ``_normalize_*`` functions across
three metric families, each deciding for itself what counts as an
insignificant difference. While that persists, the fairness guarantee holds
only for whichever metrics were remembered to route through canon — and which
ones those are is not visible from any report.
"""

from __future__ import annotations

import pytest

from arabicfinbench.canon.authority import (
    CANON_DOES_NOT_COVER,
    CANON_SUBSUMES,
    audit,
    canonical_text,
    normalize_for_comparison,
    upstream_normalizer,
)


class TestAuditCatchesDrift:
    def test_every_declared_upstream_normalizer_is_accounted_for(self) -> None:
        report = audit()
        assert report.is_complete, (
            f"upstream declares normalizers this module does not know about: "
            f"{report.unaccounted}. Each must be classified as subsumed by canon "
            f"or explicitly not covered, or a metric family will normalize "
            f"differently from every other."
        )

    def test_the_audit_reports_upstreams_actual_set(self) -> None:
        from extract_bench.test_cases.schema import EXTRACT_FIELD_NORMALIZERS

        assert set(audit().declared_upstream) == set(EXTRACT_FIELD_NORMALIZERS)

    def test_every_known_normalizer_has_a_stated_reason(self) -> None:
        # A classification with no reason is a classification nobody can check.
        for name, reason in {**CANON_SUBSUMES, **CANON_DOES_NOT_COVER}.items():
            assert reason.strip(), f"{name} is classified with no reason"

    def test_a_normalizer_cannot_be_both_subsumed_and_uncovered(self) -> None:
        assert not (set(CANON_SUBSUMES) & set(CANON_DOES_NOT_COVER))

    def test_the_audit_stamps_the_canon_version(self) -> None:
        from arabicfinbench.canon.version import CANON_VERSION

        assert audit().canon_version == CANON_VERSION


class TestSingleEntryPoint:
    def test_upstream_normalizers_are_reachable_by_name(self) -> None:
        assert upstream_normalizer("phone_digits")("+966 (11) 123-4567") == "966111234567"
        assert upstream_normalizer("case_insensitive")("ABC") == "abc"

    def test_an_unknown_normalizer_is_refused_by_name(self) -> None:
        with pytest.raises(KeyError, match="invented"):
            upstream_normalizer("invented")

    def test_canon_runs_before_upstream_normalizers(self) -> None:
        # A phone written in Arabic-Indic digits must reach phone_digits as
        # digits. If the upstream rule ran first it would strip them all.
        assert normalize_for_comparison("٩٦٦١١١٢٣٤٥٦٧", normalizers=("phone_digits",)) == "966111234567"

    def test_canon_alone_is_the_default(self) -> None:
        assert normalize_for_comparison("٨٣٩,٨٢١") == "839,821"


class TestOrderIndependence:
    """The property that makes a single authority worth having."""

    def test_canon_is_idempotent(self) -> None:
        once = canonical_text("( ٤١٥,٦٥٩ ) ريال ، نعم")
        assert canonical_text(once) == once

    def test_applying_canon_twice_changes_nothing_downstream(self) -> None:
        value = "٢٤,٠٦١,٦١٢"
        assert normalize_for_comparison(canonical_text(value)) == normalize_for_comparison(value)

    def test_the_same_pair_scores_identically_whichever_family_goes_first(self) -> None:
        # The acceptance test for item 5: scoring is invariant to the order in
        # which metric families touch the document.
        from arabicfinbench.scoring import score_document

        gt = (
            "<table><tr><th>البند</th><th>٢٠٢٤ م</th></tr>"
            "<tr><td>نقد</td><td>٨٦٦,٠٨٣</td></tr>"
            "<tr><td>فوائد</td><td>(٤١٥,٦٥٩)</td></tr></table>"
        )
        pred = (
            "<table><tr><th>البند</th><th>2024م</th></tr>"
            "<tr><td>نقد</td><td>866,083</td></tr>"
            "<tr><td>فوائد</td><td>-415,659</td></tr></table>"
        )

        first = score_document(gt, pred, source="a")
        # Pre-canonicalising the inputs must not change the canonical passes:
        # canon is idempotent and already applied internally to both sides.
        second = score_document(canonical_text(gt), canonical_text(pred), source="b")

        for pass_name in ("text", "struct"):
            for metric in ("grits_con", "table_record_match"):
                assert second.passes[pass_name][metric] == pytest.approx(first.passes[pass_name][metric], abs=1e-9), (
                    f"{metric} at {pass_name} depends on who normalized first"
                )

    def test_the_raw_pass_is_deliberately_not_invariant(self) -> None:
        # raw means "no canon". Handing it already-canonical input is a
        # different measurement, not the same one computed differently — and a
        # raw pass that ignored its input's conventions would be reporting the
        # canonical number under a raw label.
        from arabicfinbench.scoring import score_document

        gt = "<table><tr><td>نقد</td><td>٨٦٦,٠٨٣</td></tr><tr><td>مخزون</td><td>٢٤,٠٦١,٦١٢</td></tr></table>"
        pred = "<table><tr><td>نقد</td><td>866,083</td></tr><tr><td>مخزون</td><td>24,061,612</td></tr></table>"

        as_given = score_document(gt, pred, source="raw-given")
        pre_folded = score_document(canonical_text(gt), canonical_text(pred), source="raw-folded")

        assert as_given.passes["raw"]["table_record_match"] < pre_folded.passes["raw"]["table_record_match"]
        # ...while the canonical passes agree, which is the invariant that matters.
        assert as_given.passes["struct"]["table_record_match"] == pytest.approx(
            pre_folded.passes["struct"]["table_record_match"], abs=1e-9
        )

    def test_cell_metrics_agree_with_the_table_metrics_on_canon(self) -> None:
        # coverage/numeric go through the same extract_table_pairs stage, so a
        # value canon folded for one is folded for the other.
        from arabicfinbench.scoring import score_document

        gt = "<table><tr><td>نقد</td><td>٨٦٦,٠٨٣</td></tr><tr><td>مخزون</td><td>٢٤,٠٦١,٦١٢</td></tr></table>"
        pred = "<table><tr><td>نقد</td><td>866,083</td></tr><tr><td>مخزون</td><td>24,061,612</td></tr></table>"
        score = score_document(gt, pred, source="agree")
        assert score.numeric is not None and score.coverage is not None
        # Same script difference, same verdict from both views.
        assert score.numeric.value_exact_match == pytest.approx(1.0)
        assert score.coverage.coverage == pytest.approx(1.0)
        assert score.passes["struct"]["table_record_match"] == pytest.approx(1.0)


class TestUpstreamBehaviourUnchanged:
    def test_phone_digits_still_strips_non_digits(self) -> None:
        # Consolidating call sites must not alter what a normalizer does.
        assert upstream_normalizer("phone_digits")("(011) 456-7890") == "0114567890"

    def test_lenient_date_delegates_to_upstream(self) -> None:
        fn = upstream_normalizer("lenient_date")
        assert callable(fn)
        assert fn("2024-12-31")  # upstream decides the form; we only route to it
