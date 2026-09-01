#!/usr/bin/env python3
"""Run the consensus-against-GT rule over stored inference results.

When two or more independent systems agree on a cell value that differs from
the ground truth, the likeliest error is the annotator's. This prints each
flagged cell as a JSONL entry ready for ``arabicfinbench/gt/corrections.log.jsonl``
— the flag opens a pixel re-verification, and the log records the outcome;
the ground truth is never silently edited.

Grids are compared after full structural canon on every side, so a flag is
about a value, not a convention.

Usage::

    python scripts/afb_consensus.py --gt test_1/Test_1.md \\
        --pipeline llamaparse_agentic --pipeline datalab_web --test-id test_1/Test_1
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from arabicfinbench.canon import canonicalize_markup, canonicalize_structure
from arabicfinbench.canon.structure import _CELL_RE, _ROW_RE, _TABLE_RE, _TAG_RE
from arabicfinbench.gt import consensus_flags


def _grids(markup: str) -> list[list[list[str]]]:
    """Struct-canonical grids for every table in a document."""
    canonical, _, _ = canonicalize_structure(canonicalize_markup(markup))
    tables = []
    for table_html in _TABLE_RE.findall(canonical):
        rows = []
        for row_html in _ROW_RE.findall(table_html):
            rows.append([_TAG_RE.sub("", inner).strip() for _, _, inner in _CELL_RE.findall(row_html)])
        tables.append(rows)
    return tables


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt", required=True, type=Path, help="ground-truth expected_markdown file")
    ap.add_argument("--pipeline", required=True, action="append", help="pipeline (repeat; needs >= 2)")
    ap.add_argument("--test-id", required=True)
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    args = ap.parse_args()

    if len(args.pipeline) < 2:
        print("consensus needs at least two independent systems")
        return 1

    gt_grids = _grids(args.gt.read_text(encoding="utf-8"))
    systems = {}
    for pipeline in args.pipeline:
        payload = json.loads((args.output_root / pipeline / f"{args.test_id}.result.json").read_text(encoding="utf-8"))
        systems[pipeline] = _grids(payload["output"]["markdown"])

    flags = consensus_flags(gt_grids, systems)
    if not flags:
        print(f"no consensus against the ground truth across {sorted(systems)} — nothing to flag")
        return 0

    now = datetime.now(UTC).isoformat()
    for flag in flags:
        entry = {
            "flagged_at": now,
            "document": args.test_id,
            "cell": f"t{flag.table}.r{flag.row}.c{flag.col}",
            "gt_value": flag.gt_value,
            "consensus_value": flag.consensus_value,
            "agreeing_systems": list(flag.agreeing_systems),
            "status": "flagged_for_pixel_verification",
            "resolution": None,
        }
        print(json.dumps(entry, ensure_ascii=False))
    print(f"\n{len(flags)} flag(s); append the verified outcomes to arabicfinbench/gt/corrections.log.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
