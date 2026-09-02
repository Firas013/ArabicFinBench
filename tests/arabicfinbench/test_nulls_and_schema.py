"""Tests for null correctness and the schema validity gate (item 6).

The unfairness each prevents:

- **Null correctness**: an empty cell that becomes ``0`` corrupts every sum
  downstream of it, silently, and still reconciles if the system is consistent
  about it. Upstream scored one direction only.
- **Schema gate**: ``schema_valid`` was computed and reported but nothing
  rejected on it, so an extraction that does not match its own declared schema
  was scored and listed beside conforming ones as though comparable.
"""

from __future__ import annotations

import pytest

from arabicfinbench.dimensions.nulls import compute_null_correctness, is_null
from arabicfinbench.gt.schema_gate import (
    SchemaValidityError,
    gate,
    validate_extraction,
)


class TestNullDetection:
    @pytest.mark.parametrize("cell", ["", "-", "—", "null", "N/A", None, "   "])
    def test_these_state_no_value(self, cell) -> None:  # noqa: ANN001
        assert is_null(cell)

    @pytest.mark.parametrize("cell", ["0", "٠", "0.00", "٨٦٦,٠٨٣", "نقد"])
    def test_a_printed_zero_is_not_null(self, cell: str) -> None:
        # The distinction the whole metric exists to protect.
        assert not is_null(cell)


class TestNullConfusion:
    def test_a_faithful_prediction_scores_perfectly(self) -> None:
        gt = [[["نقد", "٨٦٦"], ["احتياطي", "-"]]]
        report = compute_null_correctness(gt, gt)
        assert report.null_null == 1
        assert report.accuracy == pytest.approx(1.0)
        assert report.fabrication_rate == 0.0
        assert report.drop_rate == 0.0

    def test_a_null_filled_with_zero_is_fabrication(self) -> None:
        # The finance-critical case: "-" becoming "0" corrupts every sum.
        gt = [[["نقد", "٨٦٦"], ["احتياطي", "-"]]]
        pred = [[["نقد", "٨٦٦"], ["احتياطي", "0"]]]
        report = compute_null_correctness(gt, pred)
        assert report.null_to_value == 1
        assert report.fabrication_rate == pytest.approx(1.0)
        assert report.accuracy == 0.0

    def test_a_value_nulled_out_is_a_drop(self) -> None:
        gt = [[["نقد", "٨٦٦"], ["احتياطي", "٤٥٠"]]]
        pred = [[["نقد", "٨٦٦"], ["احتياطي", "-"]]]
        report = compute_null_correctness(gt, pred)
        assert report.value_to_null == 1
        # Denominator is every non-null GT cell, labels included: 4 of them.
        assert report.drop_rate == pytest.approx(0.25)

    def test_the_two_directions_are_reported_separately(self) -> None:
        gt = [[["a", "-"], ["b", "٥"]]]
        pred = [[["a", "0"], ["b", "-"]]]
        report = compute_null_correctness(gt, pred)
        assert report.null_to_value == 1
        assert report.value_to_null == 1
        assert report.fabrication_rate == pytest.approx(1.0)
        # Three non-null GT cells ("a", "b", "٥"); one of them was nulled.
        assert report.drop_rate == pytest.approx(1 / 3)

    def test_a_missing_cell_counts_as_null_not_as_skipped(self) -> None:
        gt = [[["نقد", "٨٦٦"], ["احتياطي", "٤٥٠"]]]
        pred = [[["نقد", "٨٦٦"]]]  # second row absent entirely
        report = compute_null_correctness(gt, pred)
        assert report.value_to_null == 2

    def test_no_nulls_anywhere_is_zero_not_one(self) -> None:
        # There was no null judgement to make; crediting 1.0 would score a
        # test the system never took.
        gt = [[["نقد", "٨٦٦"]]]
        report = compute_null_correctness(gt, gt)
        assert report.considered == 0
        assert report.accuracy == 0.0

    def test_canon_does_not_fold_zero_into_null(self) -> None:
        # If canon folded these the metric would be blind to its own subject.
        gt = [[["a", "-"]]]
        pred = [[["a", "٠"]]]
        assert compute_null_correctness(gt, pred).null_to_value == 1


class TestSchemaValidation:
    SCHEMA = {
        "type": "object",
        "properties": {"total": {"type": "number"}, "currency": {"type": "string"}},
        "required": ["total", "currency"],
    }

    def test_a_conforming_extraction_is_valid(self) -> None:
        outcome = validate_extraction({"total": 100, "currency": "SAR"}, self.SCHEMA)
        assert outcome.valid
        assert outcome.checked
        assert outcome.violations == ()

    def test_violations_are_listed_with_their_paths(self) -> None:
        outcome = validate_extraction({"total": "not a number"}, self.SCHEMA)
        assert not outcome.valid
        joined = " ".join(outcome.violations)
        assert "total" in joined
        assert "currency" in joined  # the missing required field

    def test_a_missing_schema_is_not_checked_rather_than_valid(self) -> None:
        # Different states: conflating them lets an undeclared schema look
        # like a passed one.
        outcome = validate_extraction({"anything": 1}, None)
        assert not outcome.checked
        assert "nothing to validate" in outcome.summary


class TestSchemaGateRefuses:
    SCHEMA = TestSchemaValidation.SCHEMA

    def test_an_invalid_extraction_is_refused_by_name(self) -> None:
        with pytest.raises(SchemaValidityError, match="run-7"):
            gate({"total": "wrong"}, self.SCHEMA, source="run-7")

    def test_the_refusal_counts_and_lists_violations(self) -> None:
        with pytest.raises(SchemaValidityError) as excinfo:
            gate({}, self.SCHEMA, source="run-7")
        assert "violation" in str(excinfo.value)
        assert len(excinfo.value.violations) >= 2

    def test_a_conforming_extraction_passes_the_gate(self) -> None:
        outcome = gate({"total": 100, "currency": "SAR"}, self.SCHEMA, source="ok")
        assert outcome.valid

    def test_no_schema_passes_the_gate_without_claiming_validity(self) -> None:
        outcome = gate({"x": 1}, None, source="unchecked")
        assert not outcome.checked

    def test_reporting_alone_was_the_previous_behaviour(self) -> None:
        # validate_extraction reports; gate refuses. The gap between them is
        # exactly what upstream had.
        payload = {"total": "wrong"}
        assert not validate_extraction(payload, self.SCHEMA).valid  # reported
        with pytest.raises(SchemaValidityError):  # now also refused
            gate(payload, self.SCHEMA)
