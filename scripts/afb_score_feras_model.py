#!/usr/bin/env python3
"""Score the local GVP chain (``feras_model``) on the same terms as every API row.

The chain is not an ExtractBench pipeline: it runs outside the harness and
writes ``pipeline_v3.py``'s ``PAGES=...STATS=...`` text, not a
``*.result.json``. So its prediction is reassembled into markup here and handed
to the same :func:`score_document` the harness rows go through.

**The ground truth used is the sidecar ``<stem>.md``** -- byte-identical to the
``expected_markdown`` the harness gave every API system -- rather than markup
rebuilt from the raw GT JSON. Rebuilding it would produce ``<table>`` where the
sidecar emits ``<table dir="rtl">`` with ``<thead>``/``<th>``, and a row scored
against different expected markup is not comparable to the rows beside it, even
when both are "correct".

Rows are recorded with ``status="hand-imported"``: the chain's tier, cost and
latency are not verifiable the way an API row's are, so the leaderboard withholds
it by default (``afb_results.py --include-hand-imported`` shows it).

Usage::

    python scripts/afb_score_feras_model.py dataset/test_4 /tmp/afb_t4_v3.txt
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def _esc(value: object) -> str:
    return html.escape(str(value or ""))


def prediction_markup(pred_path: Path) -> str:
    """Reassemble the chain's units into markup.

    Units carry a region id, a row/column index within that region, and a
    baseline y. A region holding more than one column is a table and becomes an
    HTML table; anything else is emitted as text lines. This is the same
    reassembly ``score_doc.py`` uses, kept identical so the chain's rows stay
    comparable to the ones already in the store.
    """
    body = pred_path.read_text(encoding="utf-8")
    pages = json.loads(body.split("PAGES=", 1)[1].split("\nSTATS=", 1)[0])
    blocks: list[str] = []
    for page in pages:
        regions: dict[object, list[dict]] = {}
        for unit in page["lines"]:
            regions.setdefault(unit.get("rid"), []).append(unit)
        for _rid, units in sorted(regions.items(), key=lambda kv: min(u["y"] for u in kv[1])):
            columns = {u.get("col", 0) for u in units}
            if len(columns) > 1:
                rows: dict[int, dict[int, str]] = {}
                width = max(columns)
                for u in units:
                    rows.setdefault(u.get("row", 0), {})[u.get("col", 0)] = u["t"]
                table = "<table>"
                for index in sorted(rows):
                    cells = "".join(
                        f"<td>{_esc(rows[index].get(c, ''))}</td>" for c in range(width + 1)
                    )
                    table += f"<tr>{cells}</tr>"
                blocks.append(table + "</table>")
            else:
                for u in sorted(units, key=lambda z: (round(z["y"], 3), -z["x"])):
                    blocks.append(_esc(u["t"]))
    return "\n\n".join(blocks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_dir", type=Path, help="document directory, e.g. dataset/test_4")
    ap.add_argument("prediction", type=Path, help="pipeline_v3.py output text")
    ap.add_argument("--system", default="feras_model")
    args = ap.parse_args()

    from arabicfinbench import results
    from arabicfinbench.scoring import CANON_VERSION, score_document

    pdfs = sorted(args.input_dir.glob("*.pdf"))
    if len(pdfs) != 1:
        print(f"{args.input_dir}: expected exactly one PDF, found {len(pdfs)}")
        return 1
    stem = pdfs[0].stem
    document = f"{args.input_dir.name}/{stem}"

    expected_path = args.input_dir / f"{stem}.md"
    if not expected_path.exists():
        print(f"missing {expected_path} -- run scripts/afb_gt_to_sidecar.py first")
        return 1
    expected = expected_path.read_text(encoding="utf-8")
    predicted = prediction_markup(args.prediction)

    print(
        f"canon={CANON_VERSION}  doc={document}\n"
        f"  GT   {expected.count('<table')} tables / {len(expected)} chars  (sidecar, as served to every API row)\n"
        f"  PRED {predicted.count('<table')} tables / {len(predicted)} chars"
    )

    score = score_document(expected, predicted, source=f"{args.system}/{document}")
    row = results.from_document_score(
        score,
        system=args.system,
        document=document,
        cost_per_page_usd=0.0,  # local chain: no per-call charge
        median_latency_ms=None,
        status="hand-imported",
    )
    results.append([row])
    trm = row.passes.get("struct", {}).get("table_record_match")
    print(f"  recorded {args.system} @ canon {row.canon_version}  TRM struct={trm:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
