"""The one scoring path: symmetric canon, guarded inputs, stamped results.

Fairness principle: every point a model loses must be attributable to the
model — not to a convention, the harness, or the annotator. This module is
where that principle becomes structural rather than aspirational:

- **Symmetry is not optional.** :func:`score_document` canonicalises the ground
  truth and the prediction internally, with the same rules, in the same call.
  There is no parameter to canonicalise one side only; a caller cannot express
  the biased comparison.
- **Three passes, always together.** ``raw`` is what upstream's metrics say;
  ``text`` folds transcription conventions; ``struct`` folds table-shape
  conventions. Each pass is a defensible number and they can disagree about
  ranking — on the first benchmark document they did. Emitting one without the
  others hides which a claim rests on.
- **Script fidelity is measured on the raw output and reported separately.**
  Canon folds ٨٣٩ and 839 together so values score fairly, but a model that
  preserved the page's script deserves the credit; that credit lives in its own
  column and is never folded into a P score.
- **Broken inputs fail loudly.** Mojibake raises before any metric runs. An
  empty prediction scores zero on every dimension and says so — it is never
  dropped, never averaged around.
- **Every result is stamped** with the canon version and the named rules that
  fired per side. A side whose raw output fires no rules shares the
  annotator's conventions; that is a diagnostic worth keeping, not a score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from arabicfinbench.canon import (
    TableReport,
    canonicalize_markup_traced,
    canonicalize_structure,
)
from arabicfinbench.canon.version import CANON_VERSION
from arabicfinbench.guards import assert_clean_encoding

PASSES = ("raw", "text", "struct")

# The metrics the P axis is quoted from.
HEADLINE_METRICS = (
    "grits_con",
    "grits_trm_composite",
    "table_record_match",
    "structural_consistency",
)

_TAG_RE = re.compile(r"<[^>]*>")
_ARABIC_INDIC = set("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹")
_DIGIT_RUN_RE = re.compile(r"[0-9٠-٩۰-۹]+")


@dataclass(frozen=True)
class SideTrace:
    """What canon did to one side of one document."""

    text_rules: tuple[str, ...]
    structure_rules: tuple[str, ...]
    tables: tuple[TableReport, ...]


@dataclass(frozen=True)
class DocumentScore:
    """One document, one pipeline, all passes, stamped."""

    passes: dict[str, dict[str, float]]
    gt_trace: SideTrace
    pred_trace: SideTrace
    script_fidelity: float | None
    canon_version: str = CANON_VERSION
    empty_prediction: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def raw_to_struct_delta(self) -> dict[str, float]:
        """Per-metric raw→struct movement: the convention-mismatch diagnostic.

        Near zero means the model shares the annotator's conventions; large
        means the raw score was substantially about conventions, not reading.
        """
        raw, struct = self.passes["raw"], self.passes["struct"]
        return {m: struct[m] - raw[m] for m in raw if m in struct}


def _zero_passes() -> dict[str, dict[str, float]]:
    return {p: dict.fromkeys(HEADLINE_METRICS, 0.0) for p in PASSES}


_EMPTY_TRACE = SideTrace(text_rules=(), structure_rules=(), tables=())


def reported_score(
    passes: dict[str, dict[str, float]],
    *,
    script_fidelity: float | None = None,
    source: str,
    canon_version: str = "unknown",
) -> DocumentScore:
    """Wrap numbers reported from elsewhere, marked as not re-derived.

    Use only for a system that was run on another machine and whose output is
    unavailable. The empty traces are not an oversight: nothing was
    canonicalised here because nothing was scored here, and a reader comparing
    a row with no fired rules against rows with seven of them should be able to
    see that immediately.

    The canon version defaults to ``"unknown"`` rather than this repository's,
    because claiming the local version for a number computed elsewhere is the
    precise error the stamp exists to prevent.
    """
    return DocumentScore(
        passes={p: dict(passes.get(p, {})) for p in PASSES},
        gt_trace=_EMPTY_TRACE,
        pred_trace=_EMPTY_TRACE,
        script_fidelity=script_fidelity,
        canon_version=canon_version,
        notes=(f"externally reported: {source}; not re-derived by this repository",),
    )


def _run_of_script(run: str) -> str:
    """Classify one digit run: 'arabic-indic', 'western', or 'mixed'."""
    kinds = {("arabic-indic" if ch in _ARABIC_INDIC else "western") for ch in run}
    return kinds.pop() if len(kinds) == 1 else "mixed"


def script_fidelity(gt_markup: str, raw_pred_markup: str) -> float | None:
    """Fraction of the raw prediction's digit runs written in the page's script.

    The page's script is taken from the ground truth, which transcribes the
    page verbatim by convention (gt/CONVENTIONS.md §4). Computed on the RAW
    prediction — after canon there is nothing left to measure — and reported
    in its own column, never folded into a P score: canon deliberately stops
    value scores from depending on script, and this metric is where the
    preserved-script credit lives instead.

    Returns None when either side has no digit runs to compare.
    """
    gt_runs = _DIGIT_RUN_RE.findall(_TAG_RE.sub(" ", gt_markup or ""))
    pred_runs = _DIGIT_RUN_RE.findall(_TAG_RE.sub(" ", raw_pred_markup or ""))
    if not gt_runs or not pred_runs:
        return None
    gt_kinds = [_run_of_script(r) for r in gt_runs]
    page_script = max(set(gt_kinds), key=gt_kinds.count)
    return sum(1 for r in pred_runs if _run_of_script(r) == page_script) / len(pred_runs)


def score_document(
    expected_markup: str,
    actual_markup: str,
    *,
    evaluator=None,  # noqa: ANN001 - upstream ParseEvaluator; imported lazily
    fold_letters: bool = False,
    source: str = "document",
) -> DocumentScore:
    """Score one prediction against one ground truth, symmetrically.

    Canon is applied to both sides inside this function. By design there is no
    way to request it for one side: the biased comparison is unrepresentable.

    :param source: Label for guard errors, e.g. ``"llamaparse/test_1/Test_1"``.
    :raises MojibakeError: if either side carries a broken encoding.
    """
    assert_clean_encoding(expected_markup, source=f"ground truth: {source}")

    if not (actual_markup or "").strip():
        # Guard: an empty prediction is a zero, on the record — never a skip.
        return DocumentScore(
            passes=_zero_passes(),
            gt_trace=_EMPTY_TRACE,
            pred_trace=_EMPTY_TRACE,
            script_fidelity=None,
            empty_prediction=True,
            notes=(f"empty prediction: {source} scored zero on every dimension",),
        )

    assert_clean_encoding(actual_markup, source=f"prediction: {source}")

    from extract_bench.evaluation.evaluators.parse import ParseEvaluator  # type: ignore[import-untyped]
    from extract_bench.evaluation.metrics.parse.table_parsing import (  # type: ignore[import-untyped]
        merge_preceding_titles_into_tables,
    )

    evaluator = evaluator or ParseEvaluator()

    def run_pass(expected: str, actual: str) -> dict[str, float]:
        # Mirror the evaluator's own pre-step so the raw pass reproduces the
        # harness's published numbers rather than a near-miss of them.
        actual = merge_preceding_titles_into_tables(expected, actual)
        values = evaluator._compute_table_similarity_metrics(expected, actual)
        return {m.metric_name: m.value for m in values}

    # Text tier — both sides, same rules, same call site.
    text_expected, gt_text_fired = canonicalize_markup_traced(expected_markup, fold_letters=fold_letters)
    text_actual, pred_text_fired = canonicalize_markup_traced(actual_markup, fold_letters=fold_letters)

    # Structure tier — likewise.
    struct_expected, gt_tables, gt_struct_fired = canonicalize_structure(text_expected)
    struct_actual, pred_tables, pred_struct_fired = canonicalize_structure(text_actual)

    passes = {
        "raw": run_pass(expected_markup, actual_markup),
        "text": run_pass(text_expected, text_actual),
        "struct": run_pass(struct_expected, struct_actual),
    }

    return DocumentScore(
        passes=passes,
        gt_trace=SideTrace(gt_text_fired, gt_struct_fired, tuple(gt_tables)),
        pred_trace=SideTrace(pred_text_fired, pred_struct_fired, tuple(pred_tables)),
        script_fidelity=script_fidelity(expected_markup, actual_markup),
    )
