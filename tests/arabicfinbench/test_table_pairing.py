"""The cell metrics must score the tables GriTS paired, not tables zipped by index.

The unfairness this prevents: a system that emits one extra table early — a
split header, a stray layout block — offsets every table after it. Zipped by
position, each ground-truth table is then compared against its *neighbour*, and
figures the system read perfectly score as total misses.

This is not hypothetical. On an 11-page scanned filing every system that
completed reported ``numeric_exact = 0.0000`` while 83% of the ground truth's
figures appeared verbatim in their output; each had emitted 20–30 tables where
the ground truth has 19.

The fix reuses GriTS's own Hungarian assignment (its ``pairing`` metadata)
rather than inventing a second matching, so the cell metrics and the table
metrics cannot disagree about which table is which.
"""

from __future__ import annotations

from arabicfinbench.scoring import TableAlignment, _align_to_pairing, score_document


def _tables(*pairs: tuple[int | None, dict[int, int] | None]) -> list[TableAlignment]:
    """Table-level alignments with identity row/column maps unless given."""
    return [TableAlignment(pred_index=pred, rows=rows if rows is not None else {}, cols={}) for pred, rows in pairs]


def _table(rows: list[list[str]]) -> str:
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table>{body}</table>"


ASSETS = [["البند", "القيمة"], ["نقد وأرصدة لدى البنوك", "866,083"]]
INVENTORY = [["البند", "القيمة"], ["المخزون", "24,061,612"]]
NOISE = [["ملاحظة", "قيمة"], ["إيضاح", "12"]]


class TestAlignToPairing:
    """The reordering itself, without the cost of running GriTS."""

    def test_prediction_is_reordered_onto_ground_truth_order(self) -> None:
        gt = [[["a"]], [["b"]]]
        pred = [[["B"]], [["A"]]]  # same tables, opposite document order
        aligned = _align_to_pairing(gt, pred, _tables((1, {0: 0}), (0, {0: 0})))
        assert aligned == [[["A"]], [["B"]]]

    def test_unmatched_ground_truth_table_becomes_empty_not_borrowed(self) -> None:
        # Nothing was predicted for GT table 1. It must be a miss, never the
        # neighbouring table's content standing in for it.
        gt = [[["a"]], [["b"]]]
        pred = [[["A"]]]
        assert _align_to_pairing(gt, pred, _tables((0, {0: 0}), (None, None))) == [[["A"]], []]

    def test_extra_prediction_tables_are_dropped_not_shifted_in(self) -> None:
        gt = [[["a"]]]
        pred = [[["noise"]], [["A"]]]
        assert _align_to_pairing(gt, pred, _tables((1, {0: 0}))) == [[["A"]]]

    def test_missing_pairing_falls_back_to_index_order(self) -> None:
        pred = [[["A"]]]
        assert _align_to_pairing([[["a"]]], pred, None) is pred


class TestRowAlignmentWithinAPairedTable:
    """Rows are matched by GriTS too, not read off by position."""

    def test_an_extra_prediction_row_does_not_shift_every_row_below_it(self) -> None:
        gt = [[["assets", "100"], ["stock", "200"], ["total", "300"]]]
        # The prediction emitted a spurious first row; every real row sits one
        # lower. GriTS aligns 0->1, 1->2, 2->3.
        pred = [[["spurious", "x"], ["assets", "100"], ["stock", "200"], ["total", "300"]]]
        aligned = _align_to_pairing(gt, pred, _tables((0, {0: 1, 1: 2, 2: 3})))
        assert aligned == [[["assets", "100"], ["stock", "200"], ["total", "300"]]]

    def test_an_unalignable_row_is_empty_not_a_neighbour(self) -> None:
        gt = [[["assets", "100"], ["stock", "200"]]]
        pred = [[["assets", "100"]]]
        aligned = _align_to_pairing(gt, pred, _tables((0, {0: 0})))
        assert aligned == [[["assets", "100"], ["", ""]]]

    def test_columns_are_aligned_too(self) -> None:
        gt = [[["label", "2024"]]]
        pred = [[["2024", "label"]]]
        alignment = [TableAlignment(pred_index=0, rows={0: 0}, cols={0: 1, 1: 0})]
        assert _align_to_pairing(gt, pred, alignment) == [[["label", "2024"]]]


class TestScoredDocument:
    """End to end: an offsetting extra table must not zero the figures."""

    def test_extra_leading_table_does_not_destroy_numeric_exactness(self) -> None:
        expected = _table(ASSETS) + "\n\n" + _table(INVENTORY)
        # Same two tables, read correctly, but preceded by one the ground truth
        # does not have. Zipped by index, both real tables land one slot late.
        actual = _table(NOISE) + "\n\n" + _table(ASSETS) + "\n\n" + _table(INVENTORY)

        score = score_document(expected, actual, source="pairing-regression")

        assert score.numeric is not None
        assert score.numeric.numeric_cells > 0
        # Every figure was transcribed exactly; the offset must not be charged
        # to the model.
        assert score.numeric.value_exact_match == 1.0
        assert score.numeric.digit_cer == 0.0
        assert score.coverage is not None
        assert score.coverage.coverage == 1.0
