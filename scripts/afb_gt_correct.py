#!/usr/bin/env python3
"""Apply a ground-truth correction, and log it. Never one without the other.

``gt/CONVENTIONS.md`` forbids silently editing the ground truth: a benchmark
whose answer key changes without a record is not reproducible, and a reader who
finds a number they cannot reconcile with an earlier result has no way to learn
why. This is the only supported way to change an authored cell.

Every correction records the value it replaced, the value it installed, how the
error was established, and by what evidence. ``--expect`` is required and the
edit is refused if the cell does not currently hold that value: a correction
authored against one version of the file must not silently apply to another.

Usage::

    python scripts/afb_gt_correct.py dataset/test_6 t0.r34.c0 \\
        --expect "٣٣٧,١٢٢,٠٠٠" --to "٣٣٧,١٢٢,٠٠٧" \\
        --method pixel+arithmetic \\
        --evidence "page prints ...٠٠٧; correcting it makes column 0 current
                    liabilities sum to the printed total exactly"

    python scripts/afb_gt_correct.py dataset/test_6 --from-file corrections.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

LOG = Path("arabicfinbench/gt/corrections.log.jsonl")
REF_RE = re.compile(r"^t(\d+)\.r(\d+)\.c(\d+)$")


class CorrectionError(RuntimeError):
    """A correction that cannot be applied as written."""


def parse_ref(ref: str) -> tuple[int, int, int]:
    match = REF_RE.match(ref)
    if not match:
        raise CorrectionError(f"{ref!r}: expected the form t<table>.r<row>.c<col>")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def apply_one(
    payload: dict,
    ref: str,
    expect: str,
    new: str,
) -> str:
    """Install ``new`` at ``ref``, refusing unless the cell holds ``expect``."""
    t, r, c = parse_ref(ref)
    try:
        row = payload["tables"][t]["rows"][r]
    except (IndexError, KeyError) as exc:
        raise CorrectionError(f"{ref}: no such cell in this ground truth") from exc
    if c >= len(row):
        raise CorrectionError(f"{ref}: row has {len(row)} columns")
    current = str(row[c])
    if current != expect:
        raise CorrectionError(
            f"{ref}: expected {expect!r} but the cell holds {current!r}; "
            f"the correction was authored against a different version"
        )
    row[c] = new
    return current


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input_dir", type=Path, help="document directory, e.g. dataset/test_6")
    ap.add_argument("ref", nargs="?", help="cell reference, e.g. t0.r34.c0")
    ap.add_argument("--expect", help="value the cell must currently hold")
    ap.add_argument("--to", dest="new", help="corrected value")
    ap.add_argument("--method", default="pixel", help="how the error was established")
    ap.add_argument("--evidence", default="", help="why this correction is right")
    ap.add_argument("--from-file", type=Path, help="JSON list of {ref, expect, to, method, evidence}")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pdfs = sorted(args.input_dir.glob("*.pdf"))
    stem = pdfs[0].stem if pdfs else args.input_dir.name
    gt_path = args.input_dir / f"{stem}.json"
    if not gt_path.exists():
        print(f"no ground truth at {gt_path}")
        return 1
    document = f"{args.input_dir.name}/{stem}"

    if args.from_file:
        corrections = json.loads(args.from_file.read_text(encoding="utf-8"))
    else:
        if not (args.ref and args.expect is not None and args.new is not None):
            print("give a ref with --expect and --to, or use --from-file")
            return 1
        corrections = [
            {
                "ref": args.ref,
                "expect": args.expect,
                "to": args.new,
                "method": args.method,
                "evidence": args.evidence,
            }
        ]

    payload = json.loads(gt_path.read_text(encoding="utf-8"))
    entries = []
    for item in corrections:
        try:
            was = apply_one(payload, item["ref"], item["expect"], item["to"])
        except CorrectionError as exc:
            print(f"REFUSED {item['ref']}: {exc}")
            return 1
        entries.append(
            {
                "flagged_at": datetime.now(UTC).isoformat(),
                "document": document,
                "cell": item["ref"],
                "gt_value": was,
                "consensus_value": item["to"],
                "agreeing_systems": [],
                "status": "corrected",
                "resolution": "ground truth was wrong; corrected",
                "method": item.get("method", "pixel"),
                "note": item.get("evidence", ""),
            }
        )
        print(f"  {item['ref']}: {was!r} -> {item['to']!r}")

    if args.dry_run:
        print(f"\ndry run: {len(entries)} correction(s) not written")
        return 0

    gt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\nwrote {gt_path}")
    print(f"logged {len(entries)} correction(s) to {LOG}")
    print("re-run afb_gt_to_sidecar.py, then re-record: the answer key changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
