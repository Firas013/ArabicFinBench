"""Structural canonical forms for Arabic financial tables.

A balance sheet groups its rows under section headers — ``الموجودات المتداولة``
(current assets), ``الموجودات غير المتداولة`` (non-current assets). Two systems
can render that grouping in two ways, both correct:

- as a row carrying the label in one cell and blanks beside it, or
- as a single cell spanning the table's full width.

Neither is a record. Both are grouping context. But they occupy different
numbers of grid cells, so a grid metric that sees one on each side pairs correct
data rows against the wrong neighbours from that point on, and every row below a
section header scores as a miss. The damage is positional, not semantic, which
is why it survives text canonicalisation untouched.

The fix mirrors the numeral fold: define a canonical form and apply it to both
sides. A section row is lifted out of the grid and recorded separately, so the
remaining grid is records only, and the sections stay available as the grouping
context that concept tagging needs.

Section rows are *removed from the grid, not discarded*. :class:`Section` keeps
each label and the row it preceded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from arabicfinbench.canon.text import canonicalize

_TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.S | re.I)
_ROW_RE = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<(t[dh])\b([^>]*)>(.*?)</\1\s*>", re.S | re.I)
_COLSPAN_RE = re.compile(r"\bcolspan\s*=\s*[\"']?(\d+)", re.I)
_TAG_RE = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class Section:
    """A section header lifted out of a table's grid.

    :param label: Canonical text of the header.
    :param before_row: Index, in the section-free grid, of the row this header
        introduced. Equals the row count when the header trailed the table.
    """

    label: str
    before_row: int


@dataclass(frozen=True)
class TableReport:
    """Per-table record of what the structural canon removed."""

    rows_before: int
    rows_after: int
    sections: tuple[Section, ...] = field(default_factory=tuple)
    blank_rows: int = 0

    @property
    def sections_removed(self) -> int:
        return len(self.sections)


@dataclass(frozen=True)
class _Cell:
    text: str
    colspan: int


def _cells(row_html: str) -> list[_Cell]:
    """Return the cells of one row, with tags stripped from their text."""
    out: list[_Cell] = []
    for _, attrs, inner in _CELL_RE.findall(row_html):
        span = _COLSPAN_RE.search(attrs)
        out.append(
            _Cell(
                text=canonicalize(_TAG_RE.sub("", inner)),
                colspan=int(span.group(1)) if span else 1,
            )
        )
    return out


def _column_count(rows: list[list[_Cell]]) -> int:
    """Width of the table, taken as the widest row once colspans are counted."""
    return max((sum(c.colspan for c in r) for r in rows), default=0)


def is_section_row(cells: list[_Cell], n_cols: int) -> bool:
    """Whether a row is a section header rather than a record.

    Two shapes qualify: exactly one cell carries text, or a cell carrying text
    spans the full width of the table.
    """
    if not cells:
        return False
    non_empty = [c for c in cells if c.text]
    if len(non_empty) == 1:
        return True
    return any(c.text and c.colspan >= n_cols > 0 for c in cells)


def is_blank_row(cells: list[_Cell]) -> bool:
    """Whether a row carries no text at all.

    Parsers emit these as spacers around section breaks. They are not records
    and carry no label, so they are dropped rather than recorded as sections —
    counted separately so a document full of them cannot pass unnoticed.
    """
    return bool(cells) and not any(c.text for c in cells)


def strip_table_sections(table_html: str) -> tuple[str, TableReport]:
    """Remove section-header rows from one table, recording what was removed.

    The surviving rows are spliced out of the original markup rather than
    re-serialised, so everything the metrics read — attributes, nesting,
    whitespace — is untouched apart from the removed rows.
    """
    row_spans = [(m.start(), m.end(), m.group(0)) for m in _ROW_RE.finditer(table_html)]
    if not row_spans:
        return table_html, TableReport(rows_before=0, rows_after=0)

    parsed = [_cells(html) for _, _, html in row_spans]
    n_cols = _column_count(parsed)
    blanks = [is_blank_row(cells) for cells in parsed]
    flags = [
        # A blank row has no label, so it is never a section.
        not blank and is_section_row(cells, n_cols)
        for cells, blank in zip(parsed, blanks, strict=True)
    ]

    # A table with nothing left is a misread of the rule, not a table without
    # records; leave it alone rather than deleting it entirely.
    if all(s or b for s, b in zip(flags, blanks, strict=True)):
        return table_html, TableReport(rows_before=len(row_spans), rows_after=len(row_spans))

    sections: list[Section] = []
    blank_count = 0
    kept_so_far = 0
    pieces: list[str] = []
    cursor = 0
    for (start, end, _), cells, is_section, is_blank in zip(row_spans, parsed, flags, blanks, strict=True):
        if is_section or is_blank:
            if is_section:
                label = next((c.text for c in cells if c.text), "")
                sections.append(Section(label=label, before_row=kept_so_far))
            else:
                blank_count += 1
            pieces.append(table_html[cursor:start])
            cursor = end
        else:
            kept_so_far += 1
    pieces.append(table_html[cursor:])

    return "".join(pieces), TableReport(
        rows_before=len(row_spans),
        rows_after=kept_so_far,
        sections=tuple(sections),
        blank_rows=blank_count,
    )


def strip_sections(markup: str) -> tuple[str, list[TableReport]]:
    """Apply :func:`strip_table_sections` to every table in a markup string.

    :returns: The markup with section rows removed, and one report per table in
        document order.
    """
    reports: list[TableReport] = []

    def _replace(match: re.Match[str]) -> str:
        stripped, report = strip_table_sections(match.group(0))
        reports.append(report)
        return stripped

    return _TABLE_RE.sub(_replace, markup), reports
