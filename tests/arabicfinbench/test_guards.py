"""Tests for the fail-loudly guards.

Each pins an unfairness that was actually observed: the mojibake guard exists
because a hand-exported Datalab result arrived as UTF-8-read-as-Latin-1 and
would have scored ~0 for a parse that read the page correctly; the empty guard
exists so a blank output is a zero on the record, never a silent skip that
flatters the average.
"""

from __future__ import annotations

import pytest

from arabicfinbench.guards import (
    MojibakeError,
    assert_clean_encoding,
    is_mojibake,
    mojibake_pairs,
)

# قائمة المركز المالي, decoded as Latin-1 — the exact artefact observed.
MOJIBAKE = "ÙØ§Ø¦ÙØ© Ø§ÙÙØ±ÙØ² Ø§ÙÙØ§ÙÙ"
CLEAN_ARABIC = "قائمة المركز المالي ٨٣٩,٨٢١"
CLEAN_FRENCH = "Déjà vu — ça ira, où ça?"


class TestMojibakeDetection:
    def test_real_mojibake_is_condemned(self) -> None:
        assert is_mojibake(MOJIBAKE)
        assert mojibake_pairs(MOJIBAKE) >= 3

    def test_clean_arabic_passes(self) -> None:
        assert not is_mojibake(CLEAN_ARABIC)

    def test_accented_latin_text_is_not_condemned(self) -> None:
        # Lowercase accents are common in genuine text; the mojibake signature
        # is the uppercase Ø/Ù/Ã/Â lead byte, which is not.
        assert not is_mojibake(CLEAN_FRENCH)

    def test_empty_text_passes(self) -> None:
        assert not is_mojibake("")


class TestAssertCleanEncoding:
    def test_raises_a_named_error_with_the_source(self) -> None:
        with pytest.raises(MojibakeError, match="prediction: datalab_web"):
            assert_clean_encoding(MOJIBAKE, source="prediction: datalab_web")

    def test_clean_text_is_returned_unchanged(self) -> None:
        assert assert_clean_encoding(CLEAN_ARABIC, source="gt") == CLEAN_ARABIC


class TestScoringRefusesBrokenInput:
    """The guard wired where it matters: nothing mojibake reaches a metric."""

    def test_mojibake_prediction_fails_before_scoring(self) -> None:
        from arabicfinbench.scoring import score_document

        with pytest.raises(MojibakeError, match="prediction"):
            score_document("<table><tr><td>نقد</td></tr></table>", MOJIBAKE, source="t")

    def test_mojibake_ground_truth_fails_too(self) -> None:
        # Symmetry again: a broken GT must not quietly zero every model.
        from arabicfinbench.scoring import score_document

        with pytest.raises(MojibakeError, match="ground truth"):
            score_document(MOJIBAKE, "<table><tr><td>نقد</td></tr></table>", source="t")


class TestEmptyPredictionScoresZeroOnTheRecord:
    def test_empty_prediction_is_zero_everywhere_and_says_so(self) -> None:
        from arabicfinbench.scoring import HEADLINE_METRICS, PASSES, score_document

        score = score_document("<table><tr><td>نقد</td><td>٨٣٩</td></tr></table>", "", source="empty/doc")
        assert score.empty_prediction
        for pass_name in PASSES:
            for metric in HEADLINE_METRICS:
                assert score.passes[pass_name][metric] == 0.0
        assert any("empty/doc" in note for note in score.notes)

    def test_whitespace_only_counts_as_empty(self) -> None:
        from arabicfinbench.scoring import score_document

        assert score_document("<table><tr><td>نقد</td></tr></table>", "  \n ", source="t").empty_prediction
