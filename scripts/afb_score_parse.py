#!/usr/bin/env python3
"""Score a parse run at three levels of canonicalisation and report all three.

Upstream's table metrics compare cell text literally and cell position rigidly,
so two systems that read a page identically can score far apart for writing
``839,821`` instead of ``٨٣٩,٨٢١``, or for encoding a section header as a
full-width span instead of a sparse row. Neither difference is a reading error.

Three passes, each adding one canonical form, run over the *same* harness metric
code:

``raw``
    What upstream's metrics produce. The number an ExtractBench-style
    leaderboard would show.
``text``
    Numerals, separators, diacritics, invisible marks, spacing — applied to both
    sides. See :mod:`arabicfinbench.canon.text`.
``struct``
    Additionally lifts section-header rows out of the grid on both sides, so a
    grid metric stops pairing correct rows against the wrong neighbours. See
    :mod:`arabicfinbench.canon.structure`.

All three are reported together on purpose. Each is a defensible number and they
differ substantially; quoting one without the others hides which a claim rests
on.

The per-table block exists so the next convention mismatch of this kind surfaces
as a number rather than as a debugging session: when ``rows_gt`` and
``rows_pred`` disagree after sections are removed, the ground truth and the
system are modelling the table differently, and no text rule will close it.

The harness is untouched — this reads its outputs and calls its evaluator.

Usage::

    python scripts/afb_score_parse.py --pipeline llamaparse_agentic --input-dir test_1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from arabicfinbench.canon import TableReport, canonicalize_markup, strip_sections
from extract_bench.evaluation.evaluators.parse import ParseEvaluator
from extract_bench.evaluation.metrics.parse.table_parsing import (
    merge_preceding_titles_into_tables,
)
from extract_bench.test_cases.loader import load_test_cases

# The metrics the P axis is quoted from. Anything else the evaluator emits is
# still shown, after these.
_HEADLINE = ("grits_con", "grits_trm_composite", "table_record_match", "structural_consistency")

_PASSES = ("raw", "text", "struct")


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


def _print_metrics(title: str, passes: dict[str, dict[str, float]]) -> None:
    """Print one document's metrics across every pass, widest-first."""
    print(f"\n{title}")
    header = f"  {'metric':<26}" + "".join(f"{name:>12}" for name in _PASSES) + f"{'raw→struct':>13}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    present = [n for n in _HEADLINE if any(n in p for p in passes.values())]
    present += sorted({k for p in passes.values() for k in p} - set(present))

    for name in present:
        values = [passes[p].get(name) for p in _PASSES]
        if any(v is None for v in values):
            continue
        cells = "".join(f"{v:12.4f}" for v in values)  # type: ignore[str-format]
        delta = values[-1] - values[0]  # type: ignore[operator]
        print(f"  {name:<26}{cells}{delta:+13.4f}")


def _print_table_shapes(gt: list[TableReport], pred: list[TableReport]) -> None:
    """Print per-table row counts and section removals for both sides.

    A residual ``rows_gt``/``rows_pred`` disagreement is a modelling difference
    between the ground truth and the system, not something canon can fix.
    """
    head = (
        f"\n  {'table':<7}{'rows_gt':>9}{'rows_pred':>11}"
        f"{'sec_gt':>8}{'sec_pred':>10}{'blank_gt':>10}{'blank_pred':>12}{'aligned':>9}"
    )
    print(head)
    print("  " + "-" * (len(head) - 3))
    for i in range(max(len(gt), len(pred))):
        g = gt[i] if i < len(gt) else None
        p = pred[i] if i < len(pred) else None
        g_rows = g.rows_after if g else 0
        p_rows = p.rows_after if p else 0
        g_sec = g.sections_removed if g else 0
        p_sec = p.sections_removed if p else 0
        g_blank = g.blank_rows if g else 0
        p_blank = p.blank_rows if p else 0
        mark = "yes" if g_rows == p_rows else "NO"
        print(f"  {i:<7}{g_rows:>9}{p_rows:>11}{g_sec:>8}{p_sec:>10}{g_blank:>10}{p_blank:>12}{mark:>9}")

    aligned = sum(1 for i in range(min(len(gt), len(pred))) if gt[i].rows_after == pred[i].rows_after)
    total = max(len(gt), len(pred))
    print(f"  {aligned}/{total} tables row-aligned after section removal")


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

    evaluator = ParseEvaluator()
    # (pipeline, test_id) -> per-pass metrics, for the cross-pipeline table.
    scored: dict[tuple[str, str], dict[str, dict[str, float]]] = {}

    for pipeline in args.pipeline:
        output_dir = args.output_root / pipeline
        for case in cases:
            expected = case.expected_markdown
            if not expected:
                print(f"skipping {case.test_id}: no expected_markdown")
                continue
            try:
                actual = _load_prediction(output_dir, case.test_id)
            except FileNotFoundError as exc:
                print(f"skipping {pipeline}/{case.test_id}: {exc}")
                continue

            text_expected = canonicalize_markup(expected, fold_letters=args.fold_letters)
            text_actual = canonicalize_markup(actual, fold_letters=args.fold_letters)
            struct_expected, gt_reports = strip_sections(text_expected)
            struct_actual, pred_reports = strip_sections(text_actual)

            passes = {
                "raw": _score(evaluator, expected, actual),
                "text": _score(evaluator, text_expected, text_actual),
                "struct": _score(evaluator, struct_expected, struct_actual),
            }
            scored[pipeline, case.test_id] = passes

            _print_metrics(f"{case.test_id}   [{pipeline}]", passes)
            _print_table_shapes(gt_reports, pred_reports)

    if len(args.pipeline) > 1:
        _print_pipeline_comparison(args.pipeline, cases, scored)

    return 0


def _print_pipeline_comparison(
    pipelines: list[str],
    cases: list[Any],
    scored: dict[tuple[str, str], dict[str, dict[str, float]]],
) -> None:
    """Print a pipeline-by-pipeline table, one block per pass.

    Every pass is shown rather than only the canonical one: a ranking that flips
    between passes is telling you the systems differ by convention rather than
    by reading quality, and that is the thing worth knowing.
    """
    for case in cases:
        rows = [(p, scored[p, case.test_id]) for p in pipelines if (p, case.test_id) in scored]
        if len(rows) < 2:
            continue
        print(f"\n\npipeline comparison — {case.test_id}")
        width = max(len(p) for p, _ in rows) + 2
        for pass_name in _PASSES:
            print(f"\n  [{pass_name}]")
            head = f"  {'pipeline':<{width}}" + "".join(f"{m.replace('_', ' '):>22}" for m in _HEADLINE)
            print(head)
            print("  " + "-" * (len(head) - 2))
            for pipeline, passes in rows:
                cells = "".join(
                    f"{passes[pass_name][m]:22.4f}" if m in passes[pass_name] else f"{'-':>22}" for m in _HEADLINE
                )
                print(f"  {pipeline:<{width}}{cells}")


if __name__ == "__main__":
    raise SystemExit(main())
