#!/usr/bin/env python3
"""Import a Cohere Parse results file as a harness inference result.

Cohere's export is ``{"document": {...}, "pages": [{"page", "text",
"response": {...}, "elapsed_ms", "model"}]}``. Each page's ``text`` is the
rendered page with its tables already inline as HTML, which is what the parse
metrics consume, so pages are joined in order and used directly.

Unlike the other hand-imports, this export carries real per-page timing and a
model version (``parse-v5.0``), so those are recovered rather than left blank.
It is still stamped ``hand_imported``: no call was made from here, the mode and
cost are not verifiable, and the leaderboard needs a run it can attribute.

Encoding is forced to UTF-8 and guarded on the way in — a mojibake round-trip
scores as a catastrophic parse failure that never happened.

Usage::

    python scripts/afb_import_cohere.py <results>.json \\
        --pipeline cohere_parse_5 --test-id test_1/Test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def page_markdown(page: dict[str, Any]) -> str:
    """One page's rendered content.

    ``text`` already embeds each table as HTML; the structured ``response``
    blocks carry the same content, so preferring ``text`` avoids reassembling
    something Cohere has already assembled.
    """
    text = str(page.get("text") or "").strip()
    if text:
        return text
    # Fallback: rebuild from blocks if a page carries no rendered text.
    parts: list[str] = []
    for rendered in (page.get("response") or {}).get("pages") or []:
        for block in rendered.get("blocks") or []:
            if block.get("type") == "table":
                parts.append(str((block.get("table") or {}).get("html") or ""))
            else:
                parts.append(str((block.get("text") or {}).get("content") or ""))
    return "\n\n".join(p for p in parts if p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results", type=Path, help="Cohere Parse results JSON")
    ap.add_argument("--pipeline", required=True, help="name to record the run under")
    ap.add_argument("--test-id", required=True, help="test id, e.g. test_1/Test_1")
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    args = ap.parse_args()

    payload = json.loads(args.results.read_text(encoding="utf-8"))

    from arabicfinbench.guards import assert_clean_encoding

    assert_clean_encoding(json.dumps(payload, ensure_ascii=False)[:20000], source=f"import: {args.results.name}")

    pages = payload.get("pages") or []
    rendered = [page_markdown(p) for p in pages]
    empty = [p.get("page", i + 1) for i, (p, r) in enumerate(zip(pages, rendered, strict=True)) if not r.strip()]
    markdown = "\n\n".join(r for r in rendered if r.strip())
    if not markdown:
        print(f"{args.results}: no page content found")
        return 1

    elapsed = [float(p.get("elapsed_ms") or 0) for p in pages]
    models = sorted({str(p.get("model") or "") for p in pages if p.get("model")})
    doc = payload.get("document") or {}

    result = {
        "request": {"example_id": args.test_id},
        "pipeline_name": args.pipeline,
        "product_type": "parse",
        "raw_output": {
            "_source": args.results.name,
            "_pages": len(pages),
            "_model": ", ".join(models),
            "_total_pages": doc.get("total_pages"),
            "_processed_pages": doc.get("processed_pages"),
        },
        "provenance": {"hand_imported": True},
        "latency_in_ms": int(sum(elapsed)),
        "output": {
            "task_type": "parse",
            "example_id": args.test_id,
            "pipeline_name": args.pipeline,
            "markdown": markdown,
            "empty_pages": empty,
        },
    }

    dest = args.output_root / args.pipeline / f"{args.test_id}.result.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {dest}")
    print(f"  model: {', '.join(models) or 'unstated'}")
    print(f"  pages: {len(pages)}/{doc.get('total_pages')}   tables: {markdown.lower().count('<table')}")
    print(f"  chars: {len(markdown)}   total latency: {sum(elapsed) / 1000:.1f}s")
    print("  provenance: hand_imported (dev report only; blocked from the leaderboard)")
    if empty:
        print(f"  EMPTY pages (score zero, listed, never dropped): {empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
