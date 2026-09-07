"""Tests for the symmetric scoring path.

The guards pinned here, each with the unfairness it prevents:

- **Symmetry is structural.** Canon applied to one side only moves bias
  instead of removing it. Two tests each kill one one-sided variant: a pair
  that only scores clean if the *ground truth* was canonicalised, and a pair
  that only scores clean if the *prediction* was.
- **Script fidelity is its own column.** Canon folds ٨٣٩/839 for value
  scoring; the model that preserved the page's script keeps the credit in a
  separate, never-folded metric.
- **The rank flip reproduces.** On Test_1, raw ranked Datalab over LlamaParse
  by 0.42 and canon reversed it — because one shared the annotator's digit
  script and the other read better. The synthetic fixture reproduces that
  mechanism in CI; the real-data assertion runs when the local artefacts
  exist.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from arabicfinbench.canon.version import CANON_VERSION
from arabicfinbench.scoring import (
    HEADLINE_METRICS,
    DocumentScore,
    score_document,
    script_fidelity,
)


def _table(rows: list[list[str]], header: list[str] | None = None) -> str:
    parts = ["<table>"]
    if header:
        parts.append("<tr>" + "".join(f"<th>{c}</th>" for c in header) + "</tr>")
    for row in rows:
        parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    parts.append("</table>")
    return "".join(parts)


HEADER = ["إيضاح", "القيمة", "البند"]

GT_ARABIC = _table(
    [
        ["", "٨٣٩,٨٢١", "نقد وأرصدة لدى البنوك"],
        ["٥", "٢,٧٩٠,٣٩٤", "ذمم مدينة تجارية"],
        ["٦", "(٤١٥,٦٥٩)", "فوائد مؤجلة"],
        ["", "٢٤,٠٦١,٦١٢", "المخزون"],
        ["٨", "١١,٥٧٥,٥٠٩", "ممتلكات ومعدات"],
    ],
    HEADER,
)

# Same values, Western digits and minus-negatives: a faithful reading in a
# different convention.
PRED_WESTERN_CORRECT = _table(
    [
        ["", "839,821", "نقد وأرصدة لدى البنوك"],
        ["5", "2,790,394", "ذمم مدينة تجارية"],
        ["6", "-415,659", "فوائد مؤجلة"],
        ["", "24,061,612", "المخزون"],
        ["8", "11,575,509", "ممتلكات ومعدات"],
    ],
    HEADER,
)

# The annotator's own convention, but two values misread: a worse reading in
# the matching convention.
PRED_ARABIC_WRONG = _table(
    [
        ["", "٨٣٩,٨٢١", "نقد وأرصدة لدى البنوك"],
        ["٥", "٢,٧٩٠,٣٩٤", "ذمم مدينة تجارية"],
        ["٦", "(٤١٥,٦٥٩)", "فوائد مؤجلة"],
        ["", "٢٤,٩٦١,٦١٢", "المخزون"],  # misread digit
        ["٨", "١١,٥٧٥,٥٩٠", "ممتلكات ومعدات"],  # transposed digits
    ],
    HEADER,
)


class TestSymmetryIsStructural:
    def test_no_parameter_can_canonicalize_one_side_only(self) -> None:
        """The signature is pinned so a per-side canon knob cannot be added quietly.

        Any addition here has to be argued for. ``relations`` (added with the F
        axis) qualifies: it names identities to evaluate, and ``fold_letters``
        remains the only canon control — applied, like every other, to both
        sides inside one call.
        """
        params = set(inspect.signature(score_document).parameters)
        assert params == {
            "expected_markup",
            "actual_markup",
            "evaluator",
            "fold_letters",
            "source",
            "relations",
        }
        canon_controls = {p for p in params if "fold" in p or "canon" in p}
        assert canon_controls == {"fold_letters"}

    def test_pair_that_needs_gt_side_canon(self) -> None:
        # GT in Arabic-Indic, prediction already canonical. Canonicalising the
        # prediction only would leave the GT unfolded and score this near zero.
        score = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="sym/gt")
        assert score.passes["text"]["table_record_match"] == pytest.approx(1.0)

    def test_pair_that_needs_prediction_side_canon(self) -> None:
        # GT already canonical, prediction in Arabic-Indic with paren
        # negatives. Canonicalising the GT only would score this near zero.
        score = score_document(PRED_WESTERN_CORRECT, GT_ARABIC, source="sym/pred")
        assert score.passes["text"]["table_record_match"] == pytest.approx(1.0)

    def test_raw_pass_still_sees_the_convention_gap(self) -> None:
        # Raw stays raw: the same pair is far from perfect before canon.
        score = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="sym/raw")
        assert score.passes["raw"]["table_record_match"] < 0.7


class TestScriptFidelity:
    def test_preserving_the_page_script_scores_one(self) -> None:
        assert script_fidelity(GT_ARABIC, PRED_ARABIC_WRONG) == pytest.approx(1.0)

    def test_folding_every_digit_scores_zero(self) -> None:
        assert script_fidelity(GT_ARABIC, PRED_WESTERN_CORRECT) == pytest.approx(0.0)

    def test_no_digits_anywhere_is_not_a_score(self) -> None:
        assert script_fidelity("<p>نص بلا أرقام</p>", "<p>نص</p>") is None

    def test_fidelity_is_not_a_headline_metric(self) -> None:
        # The credit lives in its own column; it is never folded into P.
        assert "script_fidelity" not in HEADLINE_METRICS

    def test_fidelity_is_computed_on_raw_not_canon(self) -> None:
        # After canon there is nothing left to measure — the field exists on
        # the score and reflects the raw output.
        score = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="fid")
        assert score.script_fidelity == pytest.approx(0.0)
        score2 = score_document(GT_ARABIC, PRED_ARABIC_WRONG, source="fid2")
        assert score2.script_fidelity == pytest.approx(1.0)


class TestRankFlipRegression:
    """The Test_1 mechanism, reproduced synthetically for CI."""

    def test_raw_prefers_the_convention_matcher(self) -> None:
        better_reader = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="flip/a")
        convention_matcher = score_document(GT_ARABIC, PRED_ARABIC_WRONG, source="flip/b")
        metric = "table_record_match"
        assert convention_matcher.passes["raw"][metric] > better_reader.passes["raw"][metric]

    def test_canon_prefers_the_better_reader(self) -> None:
        better_reader = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="flip/a")
        convention_matcher = score_document(GT_ARABIC, PRED_ARABIC_WRONG, source="flip/b")
        metric = "table_record_match"
        assert better_reader.passes["struct"][metric] > convention_matcher.passes["struct"][metric]

    def test_the_delta_diagnostic_separates_the_two(self) -> None:
        # Near-zero delta = shares the annotator's conventions; large = does
        # not. The diagnostic must point in opposite directions for the pair.
        better_reader = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="flip/a")
        convention_matcher = score_document(GT_ARABIC, PRED_ARABIC_WRONG, source="flip/b")
        metric = "table_record_match"
        assert better_reader.raw_to_struct_delta[metric] > 0.2
        assert abs(convention_matcher.raw_to_struct_delta[metric]) < 0.1


_REPO = Path(__file__).resolve().parents[2]
_GT = _REPO / "dataset" / "test_1" / "Test_1.md"
# The second system was datalab_web, whose output was a console export with no
# stored result file, so this class skipped permanently. mistral_ocr_4 stands in
# the same relation to llamaparse_agentic -- higher raw, lower struct, and the
# opposite script behaviour -- so the two claims below are unchanged; only the
# system that demonstrates them is one whose output is actually on disk.
_LOW_RAW_HIGH_STRUCT = _REPO / "output" / "llamaparse_agentic" / "test_1" / "Test_1.result.json"
_HIGH_RAW_LOW_STRUCT = _REPO / "output" / "mistral_ocr_4" / "test_1" / "Test_1.result.json"
_REAL_RUNS = [_LOW_RAW_HIGH_STRUCT, _HIGH_RAW_LOW_STRUCT, _GT]


@pytest.mark.skipif(
    not all(p.exists() for p in _REAL_RUNS),
    reason="local Test_1 inference output not present (filings are not committed)",
)
class TestRankFlipOnStoredResults:
    """The observed numbers, re-derived from the stored local results.

    The finding this pins: on Test_1 the ranking *reverses* between the raw and
    struct passes, so quoting either alone picks a different winner. It is the
    evidence behind reporting all three passes side by side.
    """

    def _score(self, result_path: Path) -> DocumentScore:
        gt = _GT.read_text(encoding="utf-8")
        pred = json.loads(result_path.read_text(encoding="utf-8"))["output"]["markdown"]
        return score_document(gt, pred, source=result_path.parent.name)

    def test_both_orderings_reproduce(self) -> None:
        llama = self._score(_LOW_RAW_HIGH_STRUCT)
        other = self._score(_HIGH_RAW_LOW_STRUCT)
        metric = "table_record_match"
        # Raw says one system is better; canon says the other. Both are real.
        assert other.passes["raw"][metric] > llama.passes["raw"][metric]
        assert llama.passes["struct"][metric] > other.passes["struct"][metric]

    def test_the_script_fidelity_gap_reproduces(self) -> None:
        llama = self._score(_LOW_RAW_HIGH_STRUCT)
        other = self._score(_HIGH_RAW_LOW_STRUCT)
        # Canon deliberately folds digit script so values score fairly; the
        # credit for preserving it lives here instead, and separates these two.
        assert other.script_fidelity is not None and other.script_fidelity > 0.9
        assert llama.script_fidelity is not None and llama.script_fidelity < 0.5


class TestResultStamping:
    def test_every_score_carries_the_canon_version(self) -> None:
        score = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="stamp")
        assert score.canon_version == CANON_VERSION

    def test_fired_rules_are_reported_per_side(self) -> None:
        score = score_document(GT_ARABIC, PRED_WESTERN_CORRECT, source="trace")
        # The Arabic GT needed folding; the already-Western prediction did not.
        assert "text/fold_numerals" in score.gt_trace.text_rules
        assert "text/fold_numerals" not in score.pred_trace.text_rules
