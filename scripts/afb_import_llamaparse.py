#!/usr/bin/env python3
"""Import a LlamaParse job JSON as a harness inference result.

LlamaParse's job result is ``{"pages": [{"items": [...]}]}``, where each item
carries ``md`` and, for tables, an ``html`` rendering. The harness's provider
consumes the same payload; this reproduces that path for a job exported by
hand, so a run someone fetched from the LlamaCloud console scores through
exactly the same code as an API run.

Tables are taken from ``html`` where present, because that is what the
provider itself uses. Everything else contributes its ``md``.

Like the Datalab importer, the result is stamped ``hand_imported``: it is
welcome in the dev report and refused by the leaderboard, which needs the tier,
cost and latency that only an API run records. Encoding is forced to UTF-8 and
guarded, because a mojibake round-trip scores as a catastrophic parse failure
that never happened.

Usage::

    python scripts/afb_import_llamaparse.py <job>.json \\
        --pipeline llamaparse_provided --test-id test_1/Test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def page_markdown(page: dict[str, Any]) -> str:
    """Render one page: table HTML where available, item markdown otherwise."""
    parts: list[str] = []
    for item in page.get("items") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "table":
            parts.append(str(item.get("html") or item.get("md") or ""))
        else:
            text = str(item.get("md") or item.get("value") or "")
            if text:
                parts.append(text)
    return "\n\n".join(p for p in parts if p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("job", type=Path, help="LlamaParse job JSON")
    ap.add_argument("--pipeline", required=True, help="name to record the run under")
    ap.add_argument("--test-id", required=True, help="test id, e.g. test_1/Test_1")
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    args = ap.parse_args()

    job = json.loads(args.job.read_text(encoding="utf-8"))

    from arabicfinbench.guards import assert_clean_encoding

    assert_clean_encoding(json.dumps(job, ensure_ascii=False)[:20000], source=f"import: {args.job.name}")

    pages = job.get("pages") or []
    rendered = [page_markdown(p) for p in pages]
    empty_pages = [
        p.get("page_number", i) for i, (p, r) in enumerate(zip(pages, rendered, strict=True)) if not r.strip()
    ]
    markdown = "\n\n".join(r for r in rendered if r.strip())
    if not markdown:
        print(f"{args.job}: no page content found")
        return 1

    result = {
        "request": {"example_id": args.test_id},
        "pipeline_name": args.pipeline,
        "product_type": "parse",
        "raw_output": {"_source": str(args.job.name), "_pages": len(pages)},
        "provenance": {"hand_imported": True},
        "output": {
            "task_type": "parse",
            "example_id": args.test_id,
            "pipeline_name": args.pipeline,
            "markdown": markdown,
            "empty_pages": empty_pages,
        },
    }

    dest = args.output_root / args.pipeline / f"{args.test_id}.result.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {dest}")
    print(f"  pages: {len(pages)}   tables: {markdown.lower().count('<table')}   chars: {len(markdown)}")
    print("  provenance: hand_imported (dev report only; blocked from the leaderboard)")
    if empty_pages:
        print(f"  EMPTY pages (score zero, listed, never dropped): {empty_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
