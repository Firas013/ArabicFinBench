"""Structural canonical forms for Arabic financial tables.

Text canon fixes how a value is written. This tier fixes how a table is
*shaped*, for three shapes that two correct systems render differently:

Section headers
    ``الموجودات المتداولة`` is a sparse row to one system and a full-width
    ``colspan`` cell to another. Neither is a record; both are grouping
    context. They occupy different numbers of grid cells, so every row below
    one scores as a miss on a positional metric. Section rows are lifted out
    of the grid and recorded as :class:`Section` — removed from the grid,
    never discarded.

Blank spacer rows
    Parsers emit them around section breaks; annotators do not encode them.
    They carry no label, so recording them as sections would invent one; they
    are dropped and counted separately.

Column order
    An RTL page gives one system a label-first array and another label-last —
    both faithful readings. On the first benchmark document the ground truth
    itself disagreed table-to-table, and positional agreement swung between
    98% and 0% on tables whose *content* matched. The canonical order is
    computed from content, not trusted from either side: the label column is
    the one whose cell bodies are least numeric (bodies, not headers — a label
    column's header is often empty), moved to index 0; columns whose headers
    parse as dates follow in ascending date order; anything else keeps its
    original relative order in between. Applied to both sides, any two
    faithful readings land on the same grid.

All of it, like text canon, is applied to ground truth and prediction alike by
the scoring layer, and every rule that changes anything is reported by name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from arabicfinbench.canon.text import canonicalize

_TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.S | re.I)
_ROW_RE = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S | re.I)
_ROW_OPEN_RE = re.compile(r"<tr\b[^>]*>", re.I)
_CELL_RE = re.compile(r"<(t[dh])\b([^>]*)>(.*?)</\1\s*>", re.S | re.I)
_COLSPAN_RE = re.compile(r"\bcolspan\s*=\s*[\"']?(\d+)", re.I)
_TAG_RE = re.compile(r"<[^>]*>")

# A canonical cell is numeric when it is a value, a note reference, or the
# conventional dash placeholder — i.e. it contains an ASCII digit (digits are
# ASCII after text canon) and no letters, or is exactly "-".
_LETTER_RE = re.compile(r"[A-Za-z؀-ۿ]")

_MONTHS = {
    "يناير": 1,
    "فبراير": 2,
    "مارس": 3,
    "ابريل": 4,
    "أبريل": 4,
    "مايو": 5,
    "يونيو": 6,
    "يوليو": 7,
    "اغسطس": 8,
    "أغسطس": 8,
    "سبتمبر": 9,
    "اكتوبر": 10,
    "أكتوبر": 10,
    "نوفمبر": 11,
    "ديسمبر": 12,
}

# Bounded against digits rather than word characters: an attached era marker
# (``2023م``) leaves no word boundary after the year, so a plain \b never
# matches the most common header form.
_YEAR_RE = re.compile(r"(?<!\d)(1[34]\d{2}|19\d{2}|20\d{2})(?!\d)")
_DAY_RE = re.compile(r"(?<!\d)(\d{1,2})(?!\d)")


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
    """Per-table record of what the structural canon did."""

    rows_before: int
    rows_after: int
    sections: tuple[Section, ...] = field(default_factory=tuple)
    blank_rows: int = 0
    label_column: int | None = None
    column_permutation: tuple[int, ...] | None = None
    column_order_skipped: str | None = None

    @property
    def sections_removed(self) -> int:
        return len(self.sections)

    @property
    def columns_reordered(self) -> bool:
        perm = self.column_permutation
        return perm is not None and perm != tuple(range(len(perm)))


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


def _is_numeric_cell(text: str) -> bool:
    """Whether a canonical cell body is a value rather than a label."""
    if not text:
        return False
    if text == "-":
        return True
    return any(ch.isdigit() and ch.isascii() for ch in text) and not _LETTER_RE.search(text)


def _header_date_key(text: str) -> tuple[int, int, int] | None:
    """Parse ``٣١ ديسمبر ٢٠٢٤ م``-style headers into a sortable (y, m, d)."""
    canonical = canonicalize(text)
    year = _YEAR_RE.search(canonical)
    if not year:
        return None
    month = next((num for name, num in _MONTHS.items() if name in canonical), 0)
    before_year = canonical[: year.start()]
    day_match = _DAY_RE.search(before_year)
    day = int(day_match.group(1)) if day_match else 0
    return int(year.group(1)), month, day


def canonical_column_order(rows: list[list[_Cell]]) -> tuple[int, ...] | None:
    """The canonical column permutation for a rectangular grid.

    Label column (least-numeric cell *bodies*; ties break rightmost, matching
    the RTL page) to index 0; date-headed columns ascending by date at the end;
    everything else keeps its original relative order in between. Returns None
    when there are not at least two columns and two rows to order.
    """
    if len(rows) < 2 or len(rows[0]) < 2:
        return None
    n = len(rows[0])
    bodies = rows[1:]

    def non_numeric_share(col: int) -> float:
        texts = [r[col].text for r in bodies if r[col].text]
        if not texts:
            return -1.0
        return sum(1 for t in texts if not _is_numeric_cell(t)) / len(texts)

    label = max(range(n), key=lambda c: (non_numeric_share(c), c))
    others = [c for c in range(n) if c != label]
    dated = [(key, c) for c in others if (key := _header_date_key(rows[0][c].text)) is not None]
    undated = [c for c in others if all(c != dc for _, dc in dated)]
    ordered_dates = [c for _, c in sorted(dated, key=lambda kc: (kc[0], kc[1]))]
    return (label, *undated, *ordered_dates)


def strip_table_sections(table_html: str) -> tuple[str, TableReport]:
    """Remove section-header and blank rows from one table.

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
    for (start, end, _), cells, is_section, blank in zip(row_spans, parsed, flags, blanks, strict=True):
        if is_section or blank:
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


def normalize_table_columns(table_html: str, report: TableReport) -> tuple[str, TableReport]:
    """Rewrite one (section-free) table into canonical column order.

    Cells are moved verbatim — attributes and inner markup intact — only their
    order within each row changes. Ragged tables and residual colspans make a
    permutation ill-defined; those are skipped and the reason recorded, never
    silently guessed at.
    """
    row_matches = list(_ROW_RE.finditer(table_html))
    if not row_matches:
        return table_html, report

    parsed = [_cells(m.group(0)) for m in row_matches]
    widths = {len(cells) for cells in parsed}
    if len(widths) != 1:
        return table_html, replace(report, column_order_skipped="ragged")
    if any(c.colspan > 1 for cells in parsed for c in cells):
        return table_html, replace(report, column_order_skipped="colspan")

    order = canonical_column_order(parsed)
    if order is None:
        return table_html, replace(report, column_order_skipped="too-small")
    report = replace(report, label_column=order[0], column_permutation=order)
    if order == tuple(range(len(order))):
        return table_html, report

    pieces: list[str] = []
    cursor = 0
    for m in row_matches:
        row_html = m.group(0)
        cell_matches = list(_CELL_RE.finditer(row_html))
        open_tag = _ROW_OPEN_RE.match(row_html)
        assert open_tag is not None  # _ROW_RE guarantees the row opens with <tr
        rebuilt = open_tag.group(0) + "".join(cell_matches[i].group(0) for i in order) + "</tr>"
        pieces.append(table_html[cursor : m.start()])
        pieces.append(rebuilt)
        cursor = m.end()
    pieces.append(table_html[cursor:])
    return "".join(pieces), report


def canonicalize_table_structure(table_html: str) -> tuple[str, TableReport]:
    """Apply the full structural canon to one table: sections, blanks, columns."""
    stripped, report = strip_table_sections(table_html)
    return normalize_table_columns(stripped, report)


def canonicalize_structure(markup: str) -> tuple[str, list[TableReport], tuple[str, ...]]:
    """Apply the structural canon to every table in a markup string.

    :returns: The canonical markup, one report per table in document order, and
        the names of the structural rules that changed anything.
    """
    reports: list[TableReport] = []

    def _replace(match: re.Match[str]) -> str:
        out, report = canonicalize_table_structure(match.group(0))
        reports.append(report)
        return out

    out = _TABLE_RE.sub(_replace, markup)
    fired: list[str] = []
    if any(r.sections_removed for r in reports):
        fired.append("structure/sections")
    if any(r.blank_rows for r in reports):
        fired.append("structure/blank_rows")
    if any(r.columns_reordered for r in reports):
        fired.append("structure/column_order")
    return out, reports, tuple(fired)


def strip_sections(markup: str) -> tuple[str, list[TableReport]]:
    """Sections and blanks only — the structural canon minus column order."""
    reports: list[TableReport] = []

    def _replace(match: re.Match[str]) -> str:
        stripped, report = strip_table_sections(match.group(0))
        reports.append(report)
        return stripped

    return _TABLE_RE.sub(_replace, markup), reports
