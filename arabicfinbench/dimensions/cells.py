"""Cell-level P metrics: coverage and numeric exactness.

Both answer questions the table metrics cannot, because both GriTS and TRM
score a cell as a single binary outcome:

Coverage
    The silent-drop detector. A cell the system never attempted is currently
    visible only indirectly, through recall, mixed together with cells it
    attempted and got wrong. Those are different failures — one is a system
    that declined to read, the other a system that misread — and a financial
    reader needs to tell them apart. Reported per table and per page, and a
    page at zero coverage is **named**, never averaged into a mean that hides
    it.

Numeric exactness
    A model that reads every label correctly and one digit wrong in a figure
    is useless for finance, and TRM scores that cell as one miss out of many —
    the same penalty as an unreadable cell. Digit-level accuracy is computed
    over numeric cells only, on canonically folded digits, so it measures the
    figure rather than the script it was written in.

Two numbers are reported rather than one, because they answer different
questions: ``digit_cer`` is how wrong the digits are, ``value_exact_match`` is
how often the figure is exactly right. A system can have a low CER and a poor
exact-match rate (one stray digit in many figures), and for finance that is a
materially different system from one with the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from arabicfinbench.canon import canonicalize
from arabicfinbench.gt.integrity import AmountParseError, parse_amount

Grid = list[list[str]]


@dataclass(frozen=True)
class CoverageReport:
    """Coverage for one document, with the empty pages named."""

    gt_cells: int
    covered_cells: int
    per_table: tuple[tuple[int, int], ...] = field(default_factory=tuple)  # (gt, covered)
    empty_tables: tuple[int, ...] = field(default_factory=tuple)  # zero-coverage table indices

    @property
    def coverage(self) -> float:
        """Fraction of ground-truth cells for which the system produced anything."""
        return self.covered_cells / self.gt_cells if self.gt_cells else 0.0

    def table_coverage(self, index: int) -> float:
        gt, covered = self.per_table[index]
        return covered / gt if gt else 0.0


@dataclass(frozen=True)
class NumericReport:
    """Digit-level accuracy over numeric cells only."""

    numeric_cells: int
    exact_values: int
    digit_edits: int
    gt_digits: int

    @property
    def digit_cer(self) -> float:
        """Character error rate over the digits of numeric cells.

        Zero when the ground truth has no digits to be wrong about — an
        absence of evidence, reported as a perfect score only because there is
        nothing to score.
        """
        return self.digit_edits / self.gt_digits if self.gt_digits else 0.0

    @property
    def value_exact_match(self) -> float:
        return self.exact_values / self.numeric_cells if self.numeric_cells else 0.0


def is_numeric_cell(cell: str) -> bool:
    """Whether a cell is a figure rather than a label.

    Defined by parseability, not by a regex over the raw text: a cell is
    numeric exactly when :func:`parse_amount` can read it, which already
    handles both digit scripts, thousands grouping, decimal commas, and
    bracketed negatives. The conventional ``-`` placeholder is a *value* (nil)
    for arithmetic, but not a figure whose digits can be scored, so it is
    excluded here.
    """
    canonical = canonicalize(cell)
    if canonical in ("", "-"):
        return False
    try:
        parse_amount(cell)
    except AmountParseError:
        return False
    return True


def _digits(cell: str) -> str:
    """The digits of a canonical cell, script-folded, sign preserved."""
    canonical = canonicalize(cell)
    return "".join(ch for ch in canonical if ch.isdigit() or ch == "-")


def _levenshtein(a: str, b: str) -> int:
    """Edit distance. Small strings; the simple DP is the right one here."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ch_a in enumerate(a, start=1):
        current = [i]
        for j, ch_b in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # deletion
                    current[j - 1] + 1,  # insertion
                    previous[j - 1] + (ch_a != ch_b),  # substitution
                )
            )
        previous = current
    return previous[-1]


def compute_coverage(gt_tables: list[Grid], pred_tables: list[Grid]) -> CoverageReport:
    """Fraction of GT cells for which the prediction has any content.

    Compared positionally over the aligned grids the table stage already
    yields. A GT cell that is itself empty is not counted: there is nothing
    there to drop.
    """
    gt_total = 0
    covered_total = 0
    per_table: list[tuple[int, int]] = []
    empty: list[int] = []

    for t, gt_grid in enumerate(gt_tables):
        pred_grid = pred_tables[t] if t < len(pred_tables) else []
        gt_n = 0
        covered_n = 0
        for r, row in enumerate(gt_grid):
            for c, cell in enumerate(row):
                if not canonicalize(cell):
                    continue
                gt_n += 1
                try:
                    if canonicalize(pred_grid[r][c]):
                        covered_n += 1
                except IndexError:
                    pass  # no cell at that position: not covered
        per_table.append((gt_n, covered_n))
        if gt_n and covered_n == 0:
            empty.append(t)
        gt_total += gt_n
        covered_total += covered_n

    return CoverageReport(
        gt_cells=gt_total,
        covered_cells=covered_total,
        per_table=tuple(per_table),
        empty_tables=tuple(empty),
    )


def compute_numeric_exactness(gt_tables: list[Grid], pred_tables: list[Grid]) -> NumericReport:
    """Digit CER and value exact-match over numeric GT cells only.

    A numeric GT cell with no prediction counts as a full deletion — every
    digit missed — rather than being skipped, so a system cannot improve its
    CER by declining to answer.
    """
    numeric = 0
    exact = 0
    edits = 0
    gt_digit_total = 0

    for t, gt_grid in enumerate(gt_tables):
        pred_grid = pred_tables[t] if t < len(pred_tables) else []
        for r, row in enumerate(gt_grid):
            for c, cell in enumerate(row):
                if not is_numeric_cell(cell):
                    continue
                numeric += 1
                gt_digits = _digits(cell)
                gt_digit_total += len(gt_digits)
                try:
                    pred_cell = pred_grid[r][c]
                except IndexError:
                    pred_cell = ""
                pred_digits = _digits(pred_cell)
                edits += _levenshtein(gt_digits, pred_digits)
                if gt_digits and gt_digits == pred_digits:
                    exact += 1

    return NumericReport(
        numeric_cells=numeric,
        exact_values=exact,
        digit_edits=edits,
        gt_digits=gt_digit_total,
    )
