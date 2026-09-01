#!/usr/bin/env python3
"""Score a parse run twice: as the harness scored it, and under ArabicFinBench canon.

Upstream's table metrics compare cell text literally, so a system that writes
``839,821`` where the ground truth writes ``٨٣٩,٨٢١`` is scored wrong for a
number it read correctly. This script re-runs the *same* metric code over
inputs that have been canonicalised on both sides, and reports the pair, so the
gap between the two is visible rather than assumed.

Reporting both is the point. The raw score is what upstream's leaderboard would
show; the canonical score is ArabicFinBench's P axis. A single number would hide
which of the two any given claim rests on.

The harness itself is untouched — this reads its outputs and calls its
evaluator, exactly as the README's "upstream harness, unmodified" rule requires.

Usage::

    python scripts/afb_score_parse.py --pipeline llamaparse_agentic --input-dir test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arabicfinbench.canon import canonicalize_markup
from extract_bench.evaluation.evaluators.parse import ParseEvaluator
from extract_bench.evaluation.metrics.parse.table_parsing import (
    merge_preceding_titles_into_tables,
)
from extract_bench.test_cases.loader import load_test_cases

# Reported for every run. Anything else the evaluator emits is shown too, but
# these are the ones the P axis is quoted from.
_HEADLINE = ("grits_con", "grits_trm_composite", "table_record_match", "structural_consistency")


def _load_prediction(output_dir: Path, test_id: str) -> str:
    """Read the predicted markdown for one test case from a pipeline's output."""
    result_path = output_dir / f"{test_id}.result.json"
    if not result_path.exists():
        raise FileNotFoundError(f"no inference result at {result_path}; run the pipeline first")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    markdown = (payload.get("output") or {}).get("markdown")
    if not markdown:
        raise ValueError(f"{result_path} has no output.markdown")
    return str(markdown)


def _score(evaluator: ParseEvaluator, expected: str, actual: str) -> dict[str, float]:
    """Run the harness's table metrics over one expected/actual markdown pair."""
    # Mirror the evaluator's own pre-step so the raw pass reproduces the
    # harness's published numbers rather than a near-miss of them.
    actual = merge_preceding_titles_into_tables(expected, actual)
    values = evaluator._compute_table_similarity_metrics(expected, actual)
    return {m.metric_name: m.value for m in values}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pipeline", required=True, help="pipeline name (output/<pipeline>/)")
    ap.add_argument("--input-dir", required=True, type=Path, help="test-case directory")
    ap.add_argument("--output-root", type=Path, default=Path("output"), help="root of pipeline outputs")
    ap.add_argument(
        "--fold-letters",
        action="store_true",
        help="also fold alef/ya/ta-marbuta variants (lossy; reported separately)",
    )
    args = ap.parse_args()

    output_dir = args.output_root / args.pipeline
    cases = load_test_cases(args.input_dir, product_type="PARSE")
    if not cases:
        print(f"no test cases found in {args.input_dir}")
        return 1

    evaluator = ParseEvaluator()
    rows: list[tuple[str, dict[str, float], dict[str, float]]] = []

    for case in cases:
        expected = case.expected_markdown
        if not expected:
            print(f"skipping {case.test_id}: no expected_markdown")
            continue
        actual = _load_prediction(output_dir, case.test_id)

        raw = _score(evaluator, expected, actual)
        canon = _score(
            evaluator,
            canonicalize_markup(expected, fold_letters=args.fold_letters),
            canonicalize_markup(actual, fold_letters=args.fold_letters),
        )
        rows.append((case.test_id, raw, canon))

    mode = "canon+letters" if args.fold_letters else "canon"
    for test_id, raw, canon in rows:
        print(f"\n{test_id}   [{args.pipeline}]")
        print(f"  {'metric':<26} {'raw':>8} {mode:>14} {'delta':>8}")
        names: list[str] = [n for n in _HEADLINE if n in raw or n in canon]
        names += sorted((set(raw) | set(canon)) - set(names))
        for name in names:
            r, c = raw.get(name), canon.get(name)
            if r is None or c is None:
                continue
            print(f"  {name:<26} {r:8.4f} {c:14.4f} {c - r:+8.4f}")

    if len(rows) > 1:
        print(f"\naggregate over {len(rows)} documents")
        print(f"  {'metric':<26} {'raw':>8} {mode:>14} {'delta':>8}")
        for name in _HEADLINE:
            rs = [r[name] for _, r, _ in rows if name in r]
            cs = [c[name] for _, _, c in rows if name in c]
            if rs and cs:
                r, c = sum(rs) / len(rs), sum(cs) / len(cs)
                print(f"  {name:<26} {r:8.4f} {c:14.4f} {c - r:+8.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
