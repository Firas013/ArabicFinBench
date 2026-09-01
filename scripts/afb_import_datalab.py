#!/usr/bin/env python3
"""Import a Datalab JSON export as a harness inference result.

Datalab can be run from its web UI rather than through the harness's provider —
useful when the SDK is not installed, or to check a run by hand. The export is
the provider's ``json`` payload: a list of page blocks, each carrying an
``html`` rendering of that page.

This writes it into the shape the evaluator reads, so a hand-run scores through
exactly the same path as an API run and the two are comparable.

The harness's Datalab provider, configured with ``output_format="html,json"``,
scores the ``html`` field rather than ``markdown`` — see
``extract_bench/inference/providers/parse/datalab.py``. Page-level ``html``
already contains that page's headings and tables, so joining the pages
reproduces the same content.

Encoding is forced to UTF-8 on read and write. A Datalab export is UTF-8; a
mojibake round-trip through a Latin-1 console turns every Arabic cell into a
mismatch and reports it as a catastrophic parse failure, which is exactly the
false result this benchmark exists to avoid.

Usage::

    python scripts/afb_import_datalab.py <export>.json \\
        --pipeline datalab_web --test-id test_1/Test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def page_html(export: dict[str, Any]) -> list[str]:
    """Return the HTML of each page block, in document order."""
    pages: list[str] = []
    for block in export.get("children") or []:
        if not isinstance(block, dict):
            continue
        if block.get("block_type") != "Page":
            continue
        html = block.get("html") or ""
        if html:
            pages.append(str(html))
    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("export", type=Path, help="Datalab JSON export")
    ap.add_argument("--pipeline", required=True, help="name to record the run under")
    ap.add_argument("--test-id", required=True, help="test id, e.g. test_1/Test_1")
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    args = ap.parse_args()

    export = json.loads(args.export.read_text(encoding="utf-8"))

    from arabicfinbench.guards import assert_clean_encoding

    # A mojibake export would score as a catastrophic parse failure that never
    # happened; refuse it here, by name, before anything downstream sees it.
    assert_clean_encoding(json.dumps(export, ensure_ascii=False)[:20000], source=f"import: {args.export.name}")

    pages = page_html(export)
    if not pages:
        print(f"{args.export}: no Page blocks with html found")
        return 1

    empty_pages = [
        block.get("page", i)
        for i, block in enumerate(export.get("children") or [])
        if isinstance(block, dict) and block.get("block_type") == "Page" and not (block.get("html") or "").strip()
    ]
    markdown = "\n\n".join(pages)
    result = {
        "request": {"example_id": args.test_id},
        "pipeline_name": args.pipeline,
        "product_type": "parse",
        # Kept so the origin of a hand-run is never guessed at later, and so
        # the leaderboard generator can refuse it: hand imports are dev-only.
        "raw_output": {"_config": {"output_format": "html,json"}, "_source": str(args.export.name)},
        "provenance": {"hand_imported": True},
        "output": {
            "task_type": "parse",
            "example_id": args.test_id,
            "pipeline_name": args.pipeline,
            "markdown": markdown,
            # Empty pages are zeros on the record, never silently dropped.
            "empty_pages": empty_pages,
        },
    }

    dest = args.output_root / args.pipeline / f"{args.test_id}.result.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    tables = markdown.lower().count("<table")
    print(f"wrote {dest}")
    print(f"  pages: {len(pages)}   tables: {tables}   chars: {len(markdown)}")
    print("  provenance: hand_imported (dev report only; blocked from the leaderboard)")
    if empty_pages:
        print(f"  EMPTY pages (score zero, listed, never dropped): {empty_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
