#!/usr/bin/env python3
"""Convert an ArabicFinBench raw ground-truth JSON into an ExtractBench sidecar.

The raw ground truth authored for ArabicFinBench looks like::

    {"lines": [{"text": ...}], "tables": [{"rows": [[cell, ...], ...]}]}

The harness does not read that shape. It discovers a parse test case from a
``<pdf_stem>.test.json`` sidecar and scores it when the case carries either
``test_rules`` or ``expected_markdown``; ``expected_markdown`` is auto-loaded
from a plain ``<pdf_stem>.md`` next to the PDF when it is not inline. Table
metrics (TEDS / GriTS) only fire when both sides contain ``<table``, so tables
are emitted as HTML rather than pipe tables.

Cell order is preserved exactly as authored. The source rows are in visual
left-to-right order, which for these RTL statements puts the row label last;
reversing it here would silently change what GriTS compares against. The
convention is recorded in the sidecar so a later run cannot quietly disagree
about it.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def _clean(cell: Any) -> str:
    """Render one cell as escaped, whitespace-collapsed text."""
    return html.escape(" ".join(str(cell).split()))


def table_to_html(rows: list[list[Any]]) -> str:
    """Render a row matrix as an HTML table, first row as the header."""
    if not rows:
        return ""
    out = ['<table dir="rtl">']
    head, *body = rows
    out.append("<thead><tr>" + "".join(f"<th>{_clean(c)}</th>" for c in head) + "</tr></thead>")
    if body:
        out.append("<tbody>")
        out.extend("<tr>" + "".join(f"<td>{_clean(c)}</td>" for c in r) + "</tr>" for r in body)
        out.append("</tbody>")
    out.append("</table>")
    return "\n".join(out)


def build_markdown(gt: dict[str, Any]) -> str:
    """Build the expected_markdown body: text lines first, then HTML tables."""
    blocks: list[str] = []
    for line in gt.get("lines", []):
        text = " ".join(str(line.get("text", "")).split())
        if text:
            blocks.append(text)
    for table in gt.get("tables", []):
        rendered = table_to_html(table.get("rows", []))
        if rendered:
            blocks.append(rendered)
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("gt_json", type=Path, help="raw ground truth (lines/tables shape)")
    ap.add_argument("pdf", type=Path, help="document the ground truth describes")
    ap.add_argument(
        "--tags",
        default="arabic,finance,parse",
        help="comma-separated document-scoped tags for the sidecar",
    )
    args = ap.parse_args()

    gt = json.loads(args.gt_json.read_text(encoding="utf-8"))
    stem = args.pdf.with_suffix("")

    md_path = stem.with_suffix(".md")
    md_path.write_text(build_markdown(gt), encoding="utf-8")

    sidecar = {
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        # Cells keep the authored visual left-to-right order, so the row label
        # is the last column. Recorded so a re-run cannot silently flip it.
        "_afb_column_order": "visual_ltr_label_last",
        "_afb_source_gt": args.gt_json.name,
    }
    sidecar_path = stem.with_suffix("")
    sidecar_path = sidecar_path.parent / f"{sidecar_path.name}.test.json"
    sidecar_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    n_lines = len(gt.get("lines", []))
    n_tables = len(gt.get("tables", []))
    n_rows = sum(len(t.get("rows", [])) for t in gt.get("tables", []))
    print(f"wrote {md_path}  ({n_lines} lines, {n_tables} tables, {n_rows} rows)")
    print(f"wrote {sidecar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
