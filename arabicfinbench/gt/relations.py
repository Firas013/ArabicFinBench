"""The declared arithmetic identities, per document.

Authored in ground-truth coordinates (``t<table>.r<row>.c<col>``), which is the
file a person edits and can check by eye. One declaration serves both uses:

* against the ground truth it is the admission gate (``gt/integrity.admit_page``)
  -- a page whose printed totals do not reconcile is not scored, because an
  unreconciled answer key penalises every system;
* against a system's figures it is the F axis
  (``dimensions/arithmetic/score.score_relations``) -- the same identity, asked
  of the reader instead of the page.

Keeping one source for both is deliberate. A separate set of "F rules" would let
the answer key and the arithmetic test drift apart, and a benchmark whose two
halves disagree is measuring neither.

Every relation here was verified against the ground truth before being declared:
80 of 81 reconcile exactly under ``Fraction`` arithmetic. The one that does not
is recorded in ``gt/corrections.log.jsonl`` as an open flag rather than removed
-- deleting an inconvenient relation is how a benchmark stops noticing its own
defects.
"""

from __future__ import annotations


def _block(name: str, table: int, total_row: int, addend_rows: list[int], columns: list[int]) -> list[dict]:
    """One identity repeated across the period columns it applies to."""
    return [
        {
            "name": f"{name}_c{col}",
            "math_type": "block_sum",
            "total": f"t{table}.r{total_row}.c{col}",
            "addends": [f"t{table}.r{row}.c{col}" for row in addend_rows],
        }
        for col in columns
    ]


def _across(name: str, table: int, rows: list[int], total_col: int, part_cols: list[int]) -> list[dict]:
    """A total column that is the sum of the segment columns beside it."""
    return [
        {
            "name": f"{name}_r{row}",
            "math_type": "block_sum",
            "total": f"t{table}.r{row}.c{total_col}",
            "addends": [f"t{table}.r{row}.c{col}" for col in part_cols],
        }
        for row in rows
    ]


# Statement of financial position: two comparative periods.
TEST_1 = [
    *_block("current_assets", 0, 7, [2, 3, 4, 5, 6], [0, 1]),
    *_block("non_current_assets", 0, 11, [9, 10], [0, 1]),
    *_block("total_assets", 0, 12, [7, 11], [0, 1]),
    *_block("current_liabilities", 0, 20, [15, 16, 17, 18, 19], [0, 1]),
    *_block("non_current_liabilities", 0, 24, [22, 23], [0, 1]),
    *_block("total_liabilities", 0, 25, [20, 24], [0, 1]),
    *_block("total_equity", 0, 31, [27, 28, 29, 30], [0, 1]),
    *_block("liabilities_and_equity", 0, 32, [25, 31], [0, 1]),
]

# Income statement: four columns (nine-month and three-month, two years each).
# Costs are printed in parentheses and parse as negative, so each step is a sum.
TEST_2 = [
    *_block("gross_profit", 0, 6, [4, 5], [0, 1, 2, 3]),
    *_block("operating_profit", 0, 11, [6, 7, 8, 9, 10], [0, 1, 2, 3]),
    *_block("profit_before_zakat", 0, 13, [11, 12], [0, 1, 2, 3]),
    *_block("profit_for_period", 0, 15, [13, 14], [0, 1, 2, 3]),
]

# Investments by measurement category, three reporting dates.
TEST_4 = [
    *_block("investments_total", 3, 6, [1, 2, 3, 4, 5], [0, 1, 2]),
]

# Segment note. It sums both ways -- down each segment column and across into
# the total column - so every figure in the block is checked twice.
TEST_5 = [
    *_block("segment_assets", 3, 9, [3, 4, 5, 6, 7, 8], [0, 1, 2, 3]),
    *_block("segment_liabilities", 3, 15, [11, 13, 14], [0, 1, 2, 3]),
    *_across("segment_assets_across", 3, [3, 4, 5, 6, 7, 8, 9], 0, [1, 2, 3]),
    *_across("segment_liabilities_across", 3, [11, 13, 14, 15], 0, [1, 2, 3]),
]

# Statement of financial position, three comparative periods.
TEST_6 = [
    *_block("non_current_assets", 0, 8, [2, 3, 4, 5, 6, 7], [0, 1, 2]),
    *_block("current_assets", 0, 16, [9, 10, 11, 12, 13, 14, 15], [0, 1, 2]),
    *_block("total_assets", 0, 17, [8, 16], [0, 1, 2]),
    *_block("equity_attributable", 0, 24, [19, 20, 21, 22, 23], [0, 1, 2]),
    *_block("total_equity", 0, 26, [24, 25], [0, 1, 2]),
    *_block("non_current_liabilities", 0, 32, [28, 29, 30, 31], [0, 1, 2]),
    *_block("current_liabilities", 0, 39, [33, 34, 35, 36, 37, 38], [0, 1, 2]),
    *_block("total_liabilities", 0, 40, [32, 39], [0, 1, 2]),
    *_block("equity_and_liabilities", 0, 41, [26, 40], [0, 1, 2]),
]

BY_DOCUMENT: dict[str, list[dict]] = {
    "test_1/Test_1": TEST_1,
    "test_2/Test_2": TEST_2,
    "test_4/Test_4": TEST_4,
    "test_5/Test_5": TEST_5,
    "test_6/Test_6": TEST_6,
}


def for_document(document: str) -> list[dict]:
    """Declared relations for a store document id, or an empty list."""
    return BY_DOCUMENT.get(document, [])
