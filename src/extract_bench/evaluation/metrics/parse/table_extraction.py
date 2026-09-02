"""Shared table identification + parsing stage.

Run once per (expected_md, actual_md) so all table metrics consume the
same set of tables, paired the same way. Normalization stays inside each
metric — GriTS and TRM apply their own per-cell normalization downstream.

Both markup kinds are identified: HTML ``<table>`` elements and markdown pipe
tables, merged in document order so a document that mixes them is handled. This
stage previously read HTML only, which meant a markdown-emitting parser
registered zero tables and scored zero on every table metric while scoring
normally under the rule engine — indistinguishable, in a report, from a model
that read nothing.

**Both sides raise on a parse failure.** Ground-truth failures are a dataset
bug and predicted failures are a model bug, but neither is allowed to be quiet:
dropping a predicted table silently produced exactly the same score as a model
that emitted no table at all, which is the failure species this benchmark most
needs to distinguish. A caller that would rather score the document zero than
abort should catch :class:`PredictionTableParseError` and say so in the report.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from extract_bench.evaluation.metrics.parse.table_parsing import (
    TableData,
    parse_html_tables,
    parse_markdown_tables,
)

if TYPE_CHECKING:
    from extract_bench.evaluation.metrics.parse.table_title_stripping import HeaderHints


def extract_html_tables(content: str) -> list[str]:
    """Extract all top-level HTML table strings from markdown/HTML content.

    Uses depth-aware string scanning to correctly handle nested tables.
    Nested tables (inside <td> cells) are included as part of the outer
    table's HTML string, not extracted as separate entries.
    """
    if not content:
        return []

    tables: list[str] = []
    lower = content.lower()
    search_start = 0
    while True:
        start = lower.find("<table", search_start)
        if start == -1:
            break
        # Verify this is a real <table> tag, not e.g. <tabledata>
        tag_name_end = start + len("<table")
        if tag_name_end < len(lower) and lower[tag_name_end] not in (">", " ", "\t", "\n", "\r"):
            search_start = start + 1
            continue

        # Track nesting depth to find the matching </table>
        depth = 0
        pos = start
        end = -1
        while pos < len(lower):
            next_open = lower.find("<table", pos + 1)
            next_close = lower.find("</table>", pos + 1)
            if next_close == -1:
                break
            # Verify nested <table> is a real tag too
            if next_open != -1 and next_open < next_close:
                nested_name_end = next_open + len("<table")
                if nested_name_end < len(lower) and lower[nested_name_end] not in (
                    ">",
                    " ",
                    "\t",
                    "\n",
                    "\r",
                ):
                    pos = next_open  # Not a real tag, skip
                    continue
                depth += 1
                pos = next_open
            else:
                if depth == 0:
                    end = next_close + len("</table>")
                    break
                depth -= 1
                pos = next_close
        if end == -1:
            tables.append(content[start:])
            break
        tables.append(content[start:end])
        search_start = end

    return tables


class GroundTruthTableParseError(RuntimeError):
    """Raised when a ground-truth table cannot be parsed. Dataset bug."""


class PredictionTableParseError(RuntimeError):
    """Raised when a predicted table cannot be parsed. Model or format bug.

    Formerly this table was dropped and the document scored on whatever
    remained, so a parse problem and a genuine reading failure produced the
    same number.
    """


# A markdown table is a run of consecutive lines containing a pipe. This
# mirrors the grouping in ``parse_markdown_tables`` so the slices this module
# hands out are exactly the ones that parser recognises.
_PIPE_LINE = re.compile(r"^.*\|.*$")


def _html_table_spans(content: str) -> list[tuple[int, int, str]]:
    """HTML table slices as ``(start, end, text)`` offsets into ``content``."""
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for text in extract_html_tables(content):
        start = content.find(text, cursor)
        if start == -1:  # pragma: no cover - slices come from this content
            continue
        spans.append((start, start + len(text), text))
        cursor = start + len(text)
    return spans


def _markdown_table_spans(content: str, blocked: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Markdown pipe-table slices, excluding anything inside an HTML table.

    The exclusion matters for a mixed document: an HTML table's markup can
    contain pipes, and picking those up would invent a table that is already
    accounted for.
    """
    spans: list[tuple[int, int, str]] = []
    offset = 0
    run_start: int | None = None
    run_lines: list[str] = []

    def flush(end_offset: int) -> None:
        nonlocal run_start, run_lines
        if run_start is not None and len(run_lines) >= 2:
            inside = any(lo <= run_start < hi for lo, hi, _ in blocked)
            if not inside:
                spans.append((run_start, end_offset, "\n".join(run_lines)))
        run_start, run_lines = None, []

    for line in content.splitlines(keepends=True):
        stripped = line.rstrip("\n")
        if "|" in stripped and _PIPE_LINE.match(stripped):
            if run_start is None:
                run_start = offset
            run_lines.append(stripped)
        else:
            flush(offset)
        offset += len(line)
    flush(offset)
    return spans


def _render_table_html(table: TableData) -> str:
    """Minimal HTML for a markdown-sourced table.

    ``ExtractedTable.raw_html`` is carried through the title-stripping stage but
    is not re-parsed by any metric, so this exists to keep the field truthful
    rather than empty. If a future metric does read it, it reads a table.
    """
    rows = []
    for r, row in enumerate(table.data):
        tag = "th" if r in table.header_rows else "td"
        cells = "".join(f"<{tag}>{cell}</{tag}>" for cell in row)
        rows.append(f"<tr>{cells}</tr>")
    return "<table>" + "".join(rows) + "</table>"


@dataclass(frozen=True)
class ExtractedTable:
    """One table, identified once. Cell content is NOT normalized.

    - GriTS reads ``raw_html`` and runs it through its own ``html_to_cells`` +
      ``normalize_cell_text`` path (P2). In P5 it switches to reading
      ``table_data`` directly with upgraded normalization.
    - TRM reads ``table_data`` and runs it through its own ``normalize_table``
      (P3 onward).
    """

    raw_html: str
    table_data: TableData  # raw parse_html_tables output, NOT normalized
    header_hints: "HeaderHints | None" = None  # populated by strip_title_rows


@dataclass(frozen=True)
class TableExtractionCounts:
    """Per-doc table counts surfaced as MetricValues."""

    expected: int
    actual: int
    unparseable_pred: int  # dropped pred tables (gt is always 0 — they raise)


def extract_normalized_tables(
    md: str,
    *,
    side: str,  # "expected" or "actual"
    doc_id: str | None = None,
) -> tuple[list[ExtractedTable], int]:
    """Extract and parse all tables on one side of a doc, both markup kinds.

    Returns ``(tables, n_unparseable)``. ``n_unparseable`` is always 0 now:
    both sides raise on a parse failure rather than dropping the table, so a
    format problem can no longer masquerade as a reading failure. The field is
    kept because ``TableExtractionCounts`` and the ``tables_unparseable_pred``
    metric are part of the reported shape.

    Note: despite the name, this stage does **not** normalize cell content —
    each metric applies its own normalization downstream. The name is kept
    for backward compatibility with the plan.
    """
    html_spans = _html_table_spans(md)
    md_spans = _markdown_table_spans(md, html_spans)
    # Document order, so a mixed document pairs table N on one side against
    # table N on the other regardless of which markup each happens to use.
    ordered = sorted(
        [(start, text, "html") for start, _, text in html_spans]
        + [(start, text, "markdown") for start, _, text in md_spans],
        key=lambda span: span[0],
    )
    if not ordered:
        return [], 0

    # Parse each slice independently rather than calling the parser on the
    # whole doc and zipping by index. The two HTML parsers (depth-aware string
    # scanner in extract_html_tables vs. lxml/bs4 in parse_html_tables) can
    # disagree on what counts as a top-level table for malformed HTML, which
    # would silently mis-pair raw_html with table_data. Parsing each slice
    # individually makes the (raw_html, table_data) pairing correct by
    # construction, and the same holds for the markdown path.
    tables: list[ExtractedTable] = []
    for i, (_, raw, kind) in enumerate(ordered):
        parsed_one = parse_html_tables(raw) if kind == "html" else parse_markdown_tables(raw)
        if not parsed_one:
            if side == "expected":
                raise GroundTruthTableParseError(f"Failed to parse expected {kind} table {i} in doc {doc_id!r}")
            raise PredictionTableParseError(
                f"Failed to parse predicted {kind} table {i} in doc {doc_id!r}. "
                f"Dropping it would score this document as if the table were "
                f"never emitted; fix the output or handle this error explicitly."
            )
        table_data = parsed_one[0]
        raw_html = raw if kind == "html" else _render_table_html(table_data)
        tables.append(ExtractedTable(raw_html=raw_html, table_data=table_data))
    return tables, 0


def extract_table_pairs(
    expected_md: str,
    actual_md: str,
    *,
    doc_id: str | None = None,
) -> tuple[list[ExtractedTable], list[ExtractedTable], TableExtractionCounts]:
    """Extract both sides for one doc."""
    expected, _ = extract_normalized_tables(expected_md, side="expected", doc_id=doc_id)
    actual, n_unparseable_pred = extract_normalized_tables(actual_md, side="actual", doc_id=doc_id)
    counts = TableExtractionCounts(
        expected=len(expected),
        actual=len(actual),
        unparseable_pred=n_unparseable_pred,
    )
    return expected, actual, counts
