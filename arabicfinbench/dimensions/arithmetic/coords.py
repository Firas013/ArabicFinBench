"""Map an authored ground-truth cell reference onto the canonical grid.

Math rules are authored against the ground-truth JSON, because that is the file
a person reads and edits: ``t0.r34.c0`` is row 34 of table 0 as typed. The
scoring grids are canonical -- section and blank rows lifted out, columns
permuted into label-first order -- so the same cell sits somewhere else, and a
rule applied at its authored coordinates would read a different figure.

The two spaces are related by transforms that are already deterministic, so the
mapping is recomputed with the same predicates rather than recorded alongside
them. Recording it would create a second source of truth that could drift from
the canon it describes; ``TableReport`` deliberately reports what happened, not
how to invert it.

Authoring in canonical coordinates would remove this module and make every rule
unreadable to the annotator who has to check it, which is the wrong trade: the
ground truth is the artifact a human has to be able to verify by eye.
"""

from __future__ import annotations

from dataclasses import dataclass

from arabicfinbench.canon.structure import (
    _CELL_RE,
    _ROW_RE,
    _TABLE_RE,
    _Cell,
    _cells,
    _column_count,
    canonical_column_order,
    is_blank_row,
    is_section_row,
)


@dataclass(frozen=True)
class TableMap:
    """Raw-to-canonical coordinates for one table."""

    rows: dict[int, int]  # raw row index -> canonical row index (absent = lifted out)
    cols: dict[int, int]  # raw column index -> canonical column index

    def locate(self, row: int, col: int) -> tuple[int, int] | None:
        """Canonical position of an authored cell, or None if canon removed it."""
        if row not in self.rows or col not in self.cols:
            return None
        return self.rows[row], self.cols[col]


def map_table(table_html: str) -> TableMap:
    """Recompute where each authored cell of one table ends up after canon.

    Mirrors ``strip_table_sections`` then ``normalize_table_columns``: the same
    predicates, in the same order, over the same parse.
    """
    row_htmls = [m.group(0) for m in _ROW_RE.finditer(table_html)]
    parsed = [_cells(html) for html in row_htmls]
    n_cols = _column_count(parsed)

    blanks = [is_blank_row(cells) for cells in parsed]
    sections = [not blank and is_section_row(cells, n_cols) for cells, blank in zip(parsed, blanks, strict=True)]
    # strip_table_sections leaves a table alone when the rule would empty it.
    if all(s or b for s, b in zip(sections, blanks, strict=True)):
        sections = [False] * len(parsed)
        blanks = [False] * len(parsed)

    rows: dict[int, int] = {}
    kept: list[list[_Cell]] = []
    for raw_index, (cells, is_section, blank) in enumerate(zip(parsed, sections, blanks, strict=True)):
        if is_section or blank:
            continue
        rows[raw_index] = len(kept)
        kept.append(cells)

    cols = {c: c for c in range(n_cols)}
    if kept:
        widths = {len(cells) for cells in kept}
        if len(widths) > 1:  # the padding normalize_table_columns applies
            width = max(widths)
            kept = [c + [_Cell(text="", colspan=1)] * (width - len(c)) for c in kept]
        if not any(c.colspan > 1 for cells in kept for c in cells):
            order = canonical_column_order(kept)
            if order is not None:
                cols = {raw: canonical for canonical, raw in enumerate(order)}
    return TableMap(rows=rows, cols=cols)


def map_document(markup: str) -> list[TableMap]:
    """One :class:`TableMap` per table, in document order."""
    return [map_table(html) for html in _TABLE_RE.findall(markup)]


def value_at(grid: list[list[str]], row: int, col: int) -> str | None:
    """Read a canonical grid defensively; a missing cell is absent, not empty."""
    if row >= len(grid) or col >= len(grid[row]):
        return None
    return grid[row][col]


__all__ = ["TableMap", "map_table", "map_document", "value_at", "_CELL_RE"]
