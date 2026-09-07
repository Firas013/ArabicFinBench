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
from arabicfinbench.dimensions.arithmetic.score import ArithmeticReport, score_relations
from arabicfinbench.dimensions.cells import (
    CoverageReport,
    NumericReport,
    compute_coverage,
    compute_numeric_exactness,
)
from arabicfinbench.dimensions.nulls import NullReport, compute_null_correctness
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
    # Cell-level P metrics, computed on the struct-canonical grids so column
    # order and section rows cannot create false misses. None when the
    # document was not scored (empty prediction, or externally reported).
    coverage: CoverageReport | None = None
    numeric: NumericReport | None = None
    nulls: NullReport | None = None
    # F. None when the document declares no relations -- an absence of rules is
    # reported as an absence, never as a score of zero.
    arithmetic: ArithmeticReport | None = None

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


def _align_to_pairing(
    gt_grids: list[list[list[str]]],
    pred_grids: list[list[list[str]]],
    pairing: list[tuple[int, int | None]] | None,
) -> list[list[list[str]]]:
    """Reorder the prediction's grids onto the ground truth's table order.

    The cell metrics compare ``gt_grids[i]`` against ``pred_grids[i]``, which is
    only meaningful once ``i`` means the same table on both sides. It does not
    by default: ``extract_table_pairs`` returns the two sides as they were
    parsed, in document order and of different lengths, and it is GriTS that
    matches them -- a Hungarian assignment over pairwise ``grits_con``, exposed
    as its ``pairing`` metadata.

    Without this step a prediction that emits one extra table early offsets
    every table after it, and each one is scored against its neighbour. That is
    not a small error: on an 11-page filing where five systems each split or
    merged a table or two, it drove ``numeric_exact`` to 0.0000 for all of them
    while 83% of the ground truth's figures were present verbatim in their
    output.

    A ground-truth table GriTS could not match becomes an empty grid rather
    than a borrowed one: nothing was predicted for it, and that is a miss.
    """
    if not pairing:
        return pred_grids  # nothing matched; index order is all there is
    aligned: list[list[list[str]]] = [[] for _ in gt_grids]
    for gt_index, pred_index in pairing:
        if gt_index < len(aligned) and pred_index is not None and pred_index < len(pred_grids):
            aligned[gt_index] = pred_grids[pred_index]
    return aligned


def _grids(expected: str, actual: str) -> tuple[list[list[list[str]]], list[list[list[str]]]]:
    """Cell grids for both sides, from the same stage the table metrics use.

    Going through ``extract_table_pairs`` rather than parsing separately means
    coverage and numeric exactness see exactly the tables GriTS and TRM saw --
    a disagreement between the cell metrics and the table metrics would
    otherwise be unattributable. Seeing the same tables is necessary but not
    sufficient: they must also be paired the same way, which
    :func:`_align_to_pairing` does with GriTS's own assignment.
    """
    from extract_bench.evaluation.metrics.parse.table_extraction import (  # type: ignore[import-untyped]
        extract_table_pairs,
    )

    gt_tables, pred_tables, _ = extract_table_pairs(expected, actual)
    to_grid = lambda tables: [  # noqa: E731 - local shorthand, used twice
        [[str(cell) for cell in row] for row in t.table_data.data] for t in tables
    ]
    return to_grid(gt_tables), to_grid(pred_tables)


def score_document(
    expected_markup: str,
    actual_markup: str,
    *,
    evaluator=None,  # noqa: ANN001 - upstream ParseEvaluator; imported lazily
    fold_letters: bool = False,
    source: str = "document",
    relations: list[dict] | None = None,
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

    def run_pass(expected: str, actual: str) -> tuple[dict[str, float], list]:
        # Mirror the evaluator's own pre-step so the raw pass reproduces the
        # harness's published numbers rather than a near-miss of them.
        actual = merge_preceding_titles_into_tables(expected, actual)
        values = evaluator._compute_table_similarity_metrics(expected, actual)
        return {m.metric_name: m.value for m in values}, values

    def table_pairing(values: list) -> list[tuple[int, int | None]] | None:
        """GriTS's ground-truth-to-prediction table assignment, if it ran."""
        for metric in values:
            pairing = (getattr(metric, "metadata", None) or {}).get("pairing")
            if pairing:
                return [(int(g), None if p is None else int(p)) for g, p in pairing]
        return None

    # Text tier — both sides, same rules, same call site.
    text_expected, gt_text_fired = canonicalize_markup_traced(expected_markup, fold_letters=fold_letters)
    text_actual, pred_text_fired = canonicalize_markup_traced(actual_markup, fold_letters=fold_letters)

    # Structure tier — likewise.
    struct_expected, gt_tables, gt_struct_fired = canonicalize_structure(text_expected)
    struct_actual, pred_tables, pred_struct_fired = canonicalize_structure(text_actual)

    raw_pass, _ = run_pass(expected_markup, actual_markup)
    text_pass, _ = run_pass(text_expected, text_actual)
    struct_pass, struct_values = run_pass(struct_expected, struct_actual)
    passes = {"raw": raw_pass, "text": text_pass, "struct": struct_pass}

    # Cell metrics on the struct-canonical grids: column order and section
    # rows are already reconciled there, so a "missing" cell is missing rather
    # than merely somewhere else.
    #
    # The prediction is re-parsed through the evaluator's own title-merge
    # pre-step, because that is the text GriTS indexed when it built the
    # pairing; parsing the unmerged markup would number the tables differently
    # and the pairing would point at the wrong ones.
    gt_grids, pred_grids = _grids(struct_expected, merge_preceding_titles_into_tables(struct_expected, struct_actual))
    pred_grids = _align_to_pairing(gt_grids, pred_grids, table_pairing(struct_values))

    # F. Relations are authored in ground-truth coordinates, so they are mapped
    # onto the canonical grid the metrics use; the prediction is then read at
    # the same canonical position, which is exactly the correspondence the cell
    # metrics already rely on.
    arithmetic = None
    if relations:
        from arabicfinbench.dimensions.arithmetic.coords import map_document, value_at

        maps = map_document(text_expected)
        values: dict[str, str | None] = {}
        for relation in relations:
            for ref in [relation["total"], *relation["addends"]]:
                if ref in values:
                    continue
                t, r, c = _parse_ref(str(ref))
                located = maps[t].locate(r, c) if t < len(maps) else None
                values[str(ref)] = (
                    value_at(pred_grids[t], *located) if located is not None and t < len(pred_grids) else None
                )
        arithmetic = score_relations(relations, values)

    return DocumentScore(
        passes=passes,
        gt_trace=SideTrace(gt_text_fired, gt_struct_fired, tuple(gt_tables)),
        pred_trace=SideTrace(pred_text_fired, pred_struct_fired, tuple(pred_tables)),
        script_fidelity=script_fidelity(expected_markup, actual_markup),
        coverage=compute_coverage(gt_grids, pred_grids),
        numeric=compute_numeric_exactness(gt_grids, pred_grids),
        nulls=compute_null_correctness(gt_grids, pred_grids),
        arithmetic=arithmetic,
    )


_REF_RE = re.compile(r"^t(\d+)\.r(\d+)\.c(\d+)$")


def _parse_ref(ref: str) -> tuple[int, int, int]:
    """Split ``t0.r34.c1`` into ground-truth coordinates."""
    match = _REF_RE.match(ref)
    if not match:
        raise ValueError(f"{ref!r}: expected the form t<table>.r<row>.c<col>")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))
