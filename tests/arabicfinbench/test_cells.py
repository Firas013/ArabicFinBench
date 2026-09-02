"""Tests for coverage and numeric exactness.

The unfairness each prevents:

- **Coverage**: a cell a system never attempted is currently visible only
  through recall, mixed in with cells it attempted and got wrong. Declining to
  read and misreading are different failures and a financial reader must be
  able to tell them apart.
- **Numeric exactness**: TRM scores one wrong digit in a figure as a single
  binary miss — the same penalty as an unreadable cell. For finance those are
  not the same event.
"""

from __future__ import annotations

import pytest

from arabicfinbench.dimensions.cells import (
    compute_coverage,
    compute_numeric_exactness,
    is_numeric_cell,
)

GT = [
    [
        ["البند", "٢٠٢٤ م"],
        ["نقد وأرصدة لدى البنوك", "٨٦٦,٠٨٣"],
        ["المخزون", "٢٤,٠٦١,٦١٢"],
    ]
]


class TestNumericCellDetection:
    @pytest.mark.parametrize("cell", ["٨٦٦,٠٨٣", "866,083", "(٤١٥,٦٥٩)", "٠,٠٢٥٨", "٥"])
    def test_figures_are_numeric(self, cell: str) -> None:
        assert is_numeric_cell(cell)

    @pytest.mark.parametrize("cell", ["البند", "نقد وأرصدة لدى البنوك", "", "٧/١"])
    def test_labels_and_references_are_not(self, cell: str) -> None:
        assert not is_numeric_cell(cell)

    def test_the_dash_placeholder_is_not_a_scorable_figure(self) -> None:
        # It is nil for arithmetic, but it has no digits to be right about.
        assert not is_numeric_cell("-")


class TestCoverage:
    def test_a_complete_prediction_covers_everything(self) -> None:
        report = compute_coverage(GT, GT)
        assert report.coverage == pytest.approx(1.0)
        assert report.empty_tables == ()

    def test_a_dropped_cell_lowers_coverage(self) -> None:
        pred = [[row[:] for row in GT[0]]]
        pred[0][2][1] = ""  # silently drop the inventory figure
        report = compute_coverage(GT, pred)
        assert report.gt_cells == 6
        assert report.covered_cells == 5
        assert report.coverage == pytest.approx(5 / 6)

    def test_a_wrong_value_is_still_covered(self) -> None:
        # This is the whole point: coverage measures attempt, not correctness.
        pred = [[row[:] for row in GT[0]]]
        pred[0][2][1] = "٩٩٩"
        assert compute_coverage(GT, pred).coverage == pytest.approx(1.0)

    def test_a_missing_table_is_zero_coverage_and_is_named(self) -> None:
        report = compute_coverage(GT, [])
        assert report.coverage == 0.0
        assert report.empty_tables == (0,), "a zero-coverage table must be named, not averaged away"

    def test_empty_gt_cells_are_not_counted_against_anyone(self) -> None:
        gt = [[["البند", ""], ["نقد", "٨٦٦"]]]
        report = compute_coverage(gt, gt)
        assert report.gt_cells == 3  # the empty GT cell is not a droppable cell

    def test_per_table_coverage_is_reported(self) -> None:
        second = [["أ", "ب"], ["١", "٢"]]
        report = compute_coverage([GT[0], second], [GT[0], []])
        assert report.table_coverage(0) == pytest.approx(1.0)
        assert report.table_coverage(1) == 0.0
        assert report.empty_tables == (1,)

    def test_a_shorter_predicted_table_loses_the_missing_rows(self) -> None:
        pred = [GT[0][:2]]  # dropped the last row entirely
        report = compute_coverage(GT, pred)
        assert report.covered_cells == 4
        assert report.coverage == pytest.approx(4 / 6)


class TestNumericExactness:
    def test_a_perfect_read_scores_perfectly(self) -> None:
        report = compute_numeric_exactness(GT, GT)
        assert report.numeric_cells == 2
        assert report.value_exact_match == pytest.approx(1.0)
        assert report.digit_cer == pytest.approx(0.0)

    def test_script_does_not_affect_the_score(self) -> None:
        # Western digits are the same figure; canon folds before comparison.
        pred = [[["البند", "2024 م"], ["نقد وأرصدة لدى البنوك", "866,083"], ["المخزون", "24,061,612"]]]
        report = compute_numeric_exactness(GT, pred)
        assert report.value_exact_match == pytest.approx(1.0)
        assert report.digit_cer == pytest.approx(0.0)

    def test_one_wrong_digit_is_not_a_whole_cell_miss(self) -> None:
        # TRM scores this cell 0. The digit view says 1 edit in 14 digits.
        pred = [[row[:] for row in GT[0]]]
        pred[0][2][1] = "٢٤,٩٦١,٦١٢"  # 0 -> 9
        report = compute_numeric_exactness(GT, pred)
        assert report.digit_edits == 1
        assert report.digit_cer < 0.1
        assert report.value_exact_match == pytest.approx(0.5)  # 1 of 2 figures exact

    def test_a_transposition_costs_two_edits(self) -> None:
        pred = [[row[:] for row in GT[0]]]
        pred[0][1][1] = "٨٦٦,٠٣٨"  # 83 -> 38
        report = compute_numeric_exactness(GT, pred)
        assert report.digit_edits == 2

    def test_a_dropped_figure_costs_every_digit(self) -> None:
        # A system must not improve its CER by declining to answer.
        pred = [[row[:] for row in GT[0]]]
        pred[0][2][1] = ""
        report = compute_numeric_exactness(GT, pred)
        assert report.digit_edits == len("24061612")
        assert report.value_exact_match == pytest.approx(0.5)

    def test_labels_are_excluded_from_the_denominator(self) -> None:
        # Getting every label wrong must not move a numeric metric.
        pred = [[["X", "٢٠٢٤ م"], ["Y", "٨٦٦,٠٨٣"], ["Z", "٢٤,٠٦١,٦١٢"]]]
        report = compute_numeric_exactness(GT, pred)
        assert report.numeric_cells == 2
        assert report.value_exact_match == pytest.approx(1.0)

    def test_bracketed_negatives_compare_by_value(self) -> None:
        gt = [[["البند", "٢٠٢٤"], ["فوائد", "(٤١٥,٦٥٩)"]]]
        pred = [[["البند", "2024"], ["فوائد", "-415,659"]]]
        report = compute_numeric_exactness(gt, pred)
        assert report.value_exact_match == pytest.approx(1.0)

    def test_the_catastrophic_collapse_case_is_visible(self) -> None:
        # ١٥,٠٠٠,٠٠٠ -> ١٥٠ : the failure bag-of-digits would miss.
        gt = [[["البند", "٢٠٢٤"], ["ضمان", "١٥,٠٠٠,٠٠٠"]]]
        pred = [[["البند", "2024"], ["ضمان", "١٥٠"]]]
        report = compute_numeric_exactness(gt, pred)
        assert report.value_exact_match == pytest.approx(0.5)
        assert report.digit_cer > 0.4

    def test_no_numeric_cells_is_not_a_failure(self) -> None:
        gt = [[["البند", "الوصف"], ["نقد", "لا شيء"]]]
        report = compute_numeric_exactness(gt, gt)
        assert report.numeric_cells == 0
        assert report.value_exact_match == 0.0
        assert report.digit_cer == 0.0
