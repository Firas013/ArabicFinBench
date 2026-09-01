#!/usr/bin/env python3
"""Score parse runs through the one scoring path, and print all of it.

This script is deliberately thin: every number comes from
:func:`arabicfinbench.scoring.score_document`, which canonicalises the ground
truth and the prediction symmetrically (there is no way to ask it not to),
guards against mojibake, scores empty predictions as zero on the record, and
stamps each result with the canon version and the named rules that fired.

What is printed, and why:

- ``raw | text | struct`` side by side, with the raw→struct delta. The delta is
  a diagnostic: near zero means the model shares the annotator's conventions,
  large means the raw number was substantially about conventions.
- ``script_fidelity`` in its own column — credit for preserving the page's
  digit script, measured on raw output, never folded into a P score.
- Per-table ``rows_gt / rows_pred / sections / blanks / column order`` so the
  next convention mismatch surfaces as a number rather than a debugging
  session.
- The canon rules that fired per side, by name.

Usage::

    python scripts/afb_score_parse.py --pipeline llamaparse_agentic \\
        --pipeline datalab_accurate --input-dir test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from arabicfinbench.scoring import (
    HEADLINE_METRICS,
    PASSES,
    DocumentScore,
    score_document,
)
from extract_bench.test_cases.loader import load_test_cases


def _load_prediction(output_dir: Path, test_id: str) -> tuple[str, str | None]:
    """Return (markdown, failure_reason) for one stored inference result.

    A failed API call — retried by the upstream runner, then recorded with an
    error — comes back as empty markdown plus its reason, so the scorer can
    score it zero on the record rather than skipping it.
    """
    result_path = output_dir / f"{test_id}.result.json"
    if not result_path.exists():
        raise FileNotFoundError(f"no inference result at {result_path}; run the pipeline first")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    error = payload.get("error") or (payload.get("output") or {}).get("error")
    markdown = (payload.get("output") or {}).get("markdown") or ""
    if error:
        return "", str(error)
    return str(markdown), None


def _col_state(report: Any) -> str:
    if report is None:
        return "-"
    if report.column_order_skipped:
        return f"skip:{report.column_order_skipped}"
    return "moved" if report.columns_reordered else "kept"


def _print_document(title: str, score: DocumentScore) -> None:
    print(f"\n{title}   [canon {score.canon_version}]")
    for note in score.notes:
        print(f"  !! {note}")

    header = f"  {'metric':<26}" + "".join(f"{name:>12}" for name in PASSES) + f"{'raw→struct':>13}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    names = [n for n in HEADLINE_METRICS if all(n in score.passes[p] for p in PASSES)]
    names += sorted({k for p in score.passes.values() for k in p} - set(names))
    for name in names:
        values = [score.passes[p].get(name) for p in PASSES]
        if any(v is None for v in values):
            continue
        cells = "".join(f"{v:12.4f}" for v in values)  # type: ignore[str-format]
        print(f"  {name:<26}{cells}{values[-1] - values[0]:+13.4f}")  # type: ignore[operator]

    fidelity = "-" if score.script_fidelity is None else f"{score.script_fidelity:.4f}"
    print(f"  {'script_fidelity (raw)':<26}{fidelity:>12}   (own column; never folded into P)")

    for side, trace in (("gt", score.gt_trace), ("pred", score.pred_trace)):
        fired = list(trace.text_rules) + list(trace.structure_rules)
        print(f"  canon rules fired [{side}]: {', '.join(fired) if fired else '(none)'}")

    gt_tables, pred_tables = score.gt_trace.tables, score.pred_trace.tables
    if gt_tables or pred_tables:
        head = (
            f"\n  {'table':<7}{'rows_gt':>9}{'rows_pred':>11}{'sec_gt':>8}{'sec_pred':>10}"
            f"{'blank_gt':>10}{'blank_pred':>12}{'cols_gt':>10}{'cols_pred':>12}{'aligned':>9}"
        )
        print(head)
        print("  " + "-" * (len(head) - 3))
        for i in range(max(len(gt_tables), len(pred_tables))):
            g = gt_tables[i] if i < len(gt_tables) else None
            p = pred_tables[i] if i < len(pred_tables) else None
            g_rows = g.rows_after if g else 0
            p_rows = p.rows_after if p else 0
            print(
                f"  {i:<7}{g_rows:>9}{p_rows:>11}"
                f"{g.sections_removed if g else 0:>8}{p.sections_removed if p else 0:>10}"
                f"{g.blank_rows if g else 0:>10}{p.blank_rows if p else 0:>12}"
                f"{_col_state(g):>10}{_col_state(p):>12}"
                f"{'yes' if g_rows == p_rows else 'NO':>9}"
            )


def _print_comparison(
    pipelines: list[str],
    cases: list[Any],
    scored: dict[tuple[str, str], DocumentScore],
) -> None:
    """Pipeline-by-pipeline, one block per pass, plus fidelity and delta.

    Every pass is shown: a ranking that flips between passes says the systems
    differ by convention, not reading quality — the thing worth knowing.
    """
    for case in cases:
        rows = [(p, scored[p, case.test_id]) for p in pipelines if (p, case.test_id) in scored]
        if len(rows) < 2:
            continue
        print(f"\n\npipeline comparison — {case.test_id}")
        width = max(len(p) for p, _ in rows) + 2
        for pass_name in PASSES:
            print(f"\n  [{pass_name}]")
            head = f"  {'pipeline':<{width}}" + "".join(f"{m.replace('_', ' '):>22}" for m in HEADLINE_METRICS)
            print(head)
            print("  " + "-" * (len(head) - 2))
            for pipeline, score in rows:
                cells = "".join(
                    f"{score.passes[pass_name][m]:22.4f}" if m in score.passes[pass_name] else f"{'-':>22}"
                    for m in HEADLINE_METRICS
                )
                print(f"  {pipeline:<{width}}{cells}")

        print("\n  [diagnostics]")
        head = f"  {'pipeline':<{width}}{'script_fidelity':>17}{'raw→struct Δtrm':>17}"
        print(head)
        print("  " + "-" * (len(head) - 2))
        for pipeline, score in rows:
            fid = "-" if score.script_fidelity is None else f"{score.script_fidelity:.4f}"
            delta = score.raw_to_struct_delta.get("table_record_match", 0.0)
            print(f"  {pipeline:<{width}}{fid:>17}{delta:>+17.4f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pipeline",
        required=True,
        action="append",
        help="pipeline name (output/<pipeline>/); repeat to compare pipelines",
    )
    ap.add_argument("--input-dir", required=True, type=Path, help="test-case directory")
    ap.add_argument("--output-root", type=Path, default=Path("output"), help="root of pipeline outputs")
    ap.add_argument(
        "--fold-letters",
        action="store_true",
        help="also fold alef/ya/ta-marbuta variants (lossy; off by default)",
    )
    args = ap.parse_args()

    cases = load_test_cases(args.input_dir, product_type="PARSE")
    if not cases:
        print(f"no test cases found in {args.input_dir}")
        return 1

    scored: dict[tuple[str, str], DocumentScore] = {}
    for pipeline in args.pipeline:
        output_dir = args.output_root / pipeline
        for case in cases:
            expected = case.expected_markdown
            if not expected:
                print(f"skipping {case.test_id}: no expected_markdown")
                continue
            try:
                actual, failure = _load_prediction(output_dir, case.test_id)
            except FileNotFoundError as exc:
                print(f"skipping {pipeline}/{case.test_id}: {exc}")
                continue

            score = score_document(
                expected,
                actual,
                fold_letters=args.fold_letters,
                source=f"{pipeline}/{case.test_id}",
            )
            if failure:
                score = DocumentScore(
                    passes=score.passes,
                    gt_trace=score.gt_trace,
                    pred_trace=score.pred_trace,
                    script_fidelity=score.script_fidelity,
                    canon_version=score.canon_version,
                    empty_prediction=score.empty_prediction,
                    notes=(*score.notes, f"failed API call scored zero: {failure}"),
                )
            scored[pipeline, case.test_id] = score
            _print_document(f"{case.test_id}   [{pipeline}]", score)

    if len(args.pipeline) > 1:
        _print_comparison(args.pipeline, cases, scored)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
