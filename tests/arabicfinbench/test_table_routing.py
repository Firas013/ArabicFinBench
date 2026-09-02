"""Tests for markdown table routing in the shared table-extraction stage.

The unfairness this fixes: ``extract_normalized_tables`` read HTML only, so a
markdown-emitting parser registered ``tables_expected: 0`` and scored zero on
GriTS and TRM while scoring normally under the rule engine. In a report that is
indistinguishable from a model that read nothing — and every leaderboard row
from such a model was wrong in that direction.
"""

from __future__ import annotations

import pytest

from extract_bench.evaluation.metrics.parse.table_extraction import (
    GroundTruthTableParseError,
    PredictionTableParseError,
    extract_normalized_tables,
    extract_table_pairs,
)

# The same two records, in both markup kinds.
HTML_TABLE = (
    "<table>"
    "<tr><th>البند</th><th>٢٠٢٤ م</th></tr>"
    "<tr><td>نقد وأرصدة لدى البنوك</td><td>٨٦٦,٠٨٣</td></tr>"
    "<tr><td>المخزون</td><td>٢٤,٠٦١,٦١٢</td></tr>"
    "</table>"
)

MD_TABLE = "| البند | ٢٠٢٤ م |\n| --- | --- |\n| نقد وأرصدة لدى البنوك | ٨٦٦,٠٨٣ |\n| المخزون | ٢٤,٠٦١,٦١٢ |\n"


def _cells(table) -> list[list[str]]:  # noqa: ANN001 - ExtractedTable
    return [[str(c).strip() for c in row] for row in table.table_data.data]


class TestMarkdownIsFound:
    def test_a_markdown_table_is_extracted_at_all(self) -> None:
        tables, _ = extract_normalized_tables(MD_TABLE, side="actual")
        assert len(tables) == 1, "markdown pipe table was not detected"

    def test_html_still_works(self) -> None:
        tables, _ = extract_normalized_tables(HTML_TABLE, side="actual")
        assert len(tables) == 1

    def test_the_two_markups_yield_the_same_cells(self) -> None:
        html_tables, _ = extract_normalized_tables(HTML_TABLE, side="expected")
        md_tables, _ = extract_normalized_tables(MD_TABLE, side="actual")
        assert _cells(html_tables[0]) == _cells(md_tables[0])

    def test_a_markdown_table_gets_usable_raw_html(self) -> None:
        # raw_html is carried through title-stripping; empty would be a lie.
        tables, _ = extract_normalized_tables(MD_TABLE, side="actual")
        assert tables[0].raw_html.startswith("<table>")
        assert "٨٦٦,٠٨٣" in tables[0].raw_html


class TestScoringParity:
    """The acceptance test: identical content scores identically either way."""

    def test_html_gt_vs_markdown_pred_pairs_the_table(self) -> None:
        expected, actual, counts = extract_table_pairs(HTML_TABLE, MD_TABLE)
        assert counts.expected == 1
        assert counts.actual == 1, "markdown prediction registered zero tables"
        assert counts.unparseable_pred == 0

    def test_the_same_table_scores_identically_in_either_markup(self) -> None:
        from arabicfinbench.scoring import score_document

        as_html = score_document(HTML_TABLE, HTML_TABLE, source="html/html")
        as_markdown = score_document(HTML_TABLE, MD_TABLE, source="html/markdown")
        for metric in ("grits_con", "table_record_match"):
            assert as_markdown.passes["struct"][metric] == pytest.approx(as_html.passes["struct"][metric], abs=1e-9), (
                f"{metric} differs by markup alone"
            )

    def test_before_the_fix_this_would_have_been_zero(self) -> None:
        # Regression pin: a markdown prediction must not score zero tables.
        from arabicfinbench.scoring import score_document

        score = score_document(HTML_TABLE, MD_TABLE, source="regression")
        assert score.passes["struct"]["table_record_match"] > 0.9


class TestMixedMarkup:
    def test_a_document_with_both_kinds_finds_both(self) -> None:
        doc = f"عنوان\n\n{HTML_TABLE}\n\nفاصل\n\n{MD_TABLE}\n"
        tables, _ = extract_normalized_tables(doc, side="actual")
        assert len(tables) == 2

    def test_document_order_is_preserved(self) -> None:
        other_md = "| أ | ب |\n| --- | --- |\n| ١ | ٢ |\n"
        doc = f"{other_md}\n\n{HTML_TABLE}\n"
        tables, _ = extract_normalized_tables(doc, side="actual")
        assert len(tables) == 2
        # The markdown table came first in the document, so it leads.
        assert _cells(tables[0])[0][0] == "أ"

    def test_pipes_inside_html_markup_do_not_invent_a_table(self) -> None:
        doc = "<table><tr><td>a | b</td><td>c</td></tr><tr><td>d</td><td>e</td></tr></table>"
        tables, _ = extract_normalized_tables(doc, side="actual")
        assert len(tables) == 1


class TestFailuresAreLoudOnBothSides:
    """lxml recovers even severely malformed table markup, so an unparseable
    table cannot be written as a literal fixture. The parser is stubbed to
    return nothing, which is the condition the code branches on."""

    @pytest.fixture()
    def unparseable(self, monkeypatch: pytest.MonkeyPatch) -> str:
        monkeypatch.setattr(
            "extract_bench.evaluation.metrics.parse.table_extraction.parse_html_tables",
            lambda _: [],
        )
        return HTML_TABLE

    def test_ground_truth_failure_still_raises(self, unparseable: str) -> None:
        with pytest.raises(GroundTruthTableParseError):
            extract_normalized_tables(unparseable, side="expected", doc_id="d1")

    def test_prediction_failure_now_raises_instead_of_dropping(self, unparseable: str) -> None:
        # This is the asymmetry fix: silently dropping scored a format bug
        # exactly like a model that emitted nothing.
        with pytest.raises(PredictionTableParseError, match="Dropping it would score"):
            extract_normalized_tables(unparseable, side="actual", doc_id="d1")

    def test_the_error_names_the_document_and_markup_kind(self, unparseable: str) -> None:
        with pytest.raises(PredictionTableParseError, match="html table 0 in doc 'd1'"):
            extract_normalized_tables(unparseable, side="actual", doc_id="d1")


class TestNoTablesIsNotAFailure:
    def test_prose_yields_no_tables_and_no_error(self) -> None:
        tables, unparseable = extract_normalized_tables("نص بلا جداول", side="actual")
        assert tables == []
        assert unparseable == 0

    def test_a_single_pipe_line_is_not_a_table(self) -> None:
        tables, _ = extract_normalized_tables("a | b\n\nplain text", side="actual")
        assert tables == []
