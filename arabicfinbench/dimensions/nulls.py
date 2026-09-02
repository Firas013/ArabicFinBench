"""Null correctness: the full confusion, not one direction.

The most finance-specific metric in the set. An empty cell that becomes ``0``
corrupts every sum downstream of it — silently, and in a way that still
reconciles if the system is consistent about it — which is why the extraction
prompt forbids it. The reverse, a real ``0`` reported as null, destroys a
figure that was printed on the page.

Upstream scores one direction: ``null_hallucination_rate`` catches a value
invented where the ground truth is null. This scores the whole confusion as a
category, because the three outcomes are different failures with different
consequences:

===================  =========================  ==============================
ground truth         prediction                 outcome
===================  =========================  ==============================
null                 null                       ``null_null`` — correct
null                 a value                    ``null_to_value`` — fabricated
a value              null                       ``value_to_null`` — dropped
===================  =========================  ==============================

The distinction ``0`` is not ``null`` is load-bearing here and is *not*
canonicalised away: an empty cell and a printed zero are different claims about
the page, and folding them would erase exactly the error this metric exists to
find.
"""

from __future__ import annotations

from dataclasses import dataclass

from arabicfinbench.canon import canonicalize

# Cell contents that represent "no value stated". The conventional dash is
# included: on a financial statement it means nil, printed. An explicit "0" is
# NOT included — a printed zero is a stated figure.
_NULL_FORMS = frozenset({"", "-", "—", "–", "null", "none", "n/a"})


def is_null(cell: str | None) -> bool:
    """Whether a cell states no value.

    ``0`` is emphatically not null. That is the whole point of the metric.
    """
    if cell is None:
        return True
    return canonicalize(cell).casefold() in _NULL_FORMS


@dataclass(frozen=True)
class NullReport:
    """The three-way confusion over cells where either side is null."""

    null_null: int = 0
    null_to_value: int = 0  # fabricated: GT had nothing, system produced a figure
    value_to_null: int = 0  # dropped: GT had a figure, system produced nothing
    value_value: int = 0  # neither side null; counted for the denominator only

    @property
    def considered(self) -> int:
        """Cells where at least one side is null — the cells this metric judges."""
        return self.null_null + self.null_to_value + self.value_to_null

    @property
    def accuracy(self) -> float:
        """Fraction of null-involving cells the system got right.

        Zero when no cell on either side is null: there was no null judgement
        to make, and claiming 1.0 would credit the system for a test it never
        took.
        """
        return self.null_null / self.considered if self.considered else 0.0

    @property
    def fabrication_rate(self) -> float:
        """Share of ground-truth nulls the system filled in.

        The direction that corrupts sums, and the one that reconciles anyway
        if the system is consistent — so it must be reported on its own.
        """
        gt_nulls = self.null_null + self.null_to_value
        return self.null_to_value / gt_nulls if gt_nulls else 0.0

    @property
    def drop_rate(self) -> float:
        """Share of ground-truth values the system nulled out."""
        gt_values = self.value_to_null + self.value_value
        return self.value_to_null / gt_values if gt_values else 0.0


def compute_null_correctness(
    gt_tables: list[list[list[str]]],
    pred_tables: list[list[list[str]]],
) -> NullReport:
    """Score the null confusion positionally over aligned grids.

    A cell the prediction does not have at all counts as null: the system
    produced no value for it, which is the same claim as an empty cell and
    must not be skipped.
    """
    null_null = null_to_value = value_to_null = value_value = 0

    for t, gt_grid in enumerate(gt_tables):
        pred_grid = pred_tables[t] if t < len(pred_tables) else []
        for r, row in enumerate(gt_grid):
            for c, gt_cell in enumerate(row):
                try:
                    pred_cell: str | None = pred_grid[r][c]
                except IndexError:
                    pred_cell = None
                gt_null, pred_null = is_null(gt_cell), is_null(pred_cell)
                if gt_null and pred_null:
                    null_null += 1
                elif gt_null and not pred_null:
                    null_to_value += 1
                elif not gt_null and pred_null:
                    value_to_null += 1
                else:
                    value_value += 1

    return NullReport(
        null_null=null_null,
        null_to_value=null_to_value,
        value_to_null=value_to_null,
        value_value=value_value,
    )
