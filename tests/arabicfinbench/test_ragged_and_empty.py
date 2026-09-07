"""Two guards that were failing open: ragged column ordering, and empty predictions.

Both let a system lose points for something that is not reading quality.

**Ragged tables.** ``normalize_table_columns`` used to decline on a table whose
rows had uneven widths. The rule runs on both sides, so it fired on the
rectangular ground truth and skipped a prediction with one uneven row, leaving
the two in different column frames. Canon was symmetric by construction and
asymmetric in effect.

**Empty predictions.** ``score_document`` detects an empty prediction and zeroes
it, but nothing forced the stored row to say so, and a zeroed ``api`` row ranks
as a measurement. "Transcribes nothing correctly" and "returned nothing" are
different claims about a system.
"""

from __future__ import annotations

from arabicfinbench.canon.structure import canonicalize_table_structure
from arabicfinbench.results import from_document_score
from arabicfinbench.scoring import score_document

RECTANGULAR = (
    "<table>"
    "<tr><td>٢٠٢٣ م</td><td>٢٠٢٤ م</td><td>الموجودات</td></tr>"
    "<tr><td>٨٣٩</td><td>٨٦٦</td><td>نقد وأرصدة</td></tr>"
    "<tr><td>٤١٥</td><td>١٩٧</td><td>ذمم مدينة</td></tr>"
    "</table>"
)

# The same three records, but one row stopped a cell short -- the shape a model
# emits when it drops a trailing empty cell.
RAGGED = (
    "<table>"
    "<tr><td>٢٠٢٣ م</td><td>٢٠٢٤ م</td><td>الموجودات</td></tr>"
    "<tr><td>٨٣٩</td><td>٨٦٦</td><td>نقد وأرصدة</td></tr>"
    "<tr><td>٤١٥</td><td>١٩٧</td></tr>"
    "</table>"
)


class TestRaggedTablesAreOrdered:
    def test_a_ragged_table_is_no_longer_skipped(self) -> None:
        _, report = canonicalize_table_structure(RAGGED)
        assert report.column_order_skipped is None
        assert report.padded_rows == 1
        assert report.column_permutation is not None

    def test_padding_reaches_the_markup(self) -> None:
        # The cell metrics read the emitted grid; a row left short there is an
        # uncovered cell rather than an empty one.
        html, _ = canonicalize_table_structure(RAGGED)
        rows = html.count("<tr")
        assert html.count("<td") == rows * 3

    def test_ragged_and_rectangular_reach_the_same_column_order(self) -> None:
        _, rect = canonicalize_table_structure(RECTANGULAR)
        _, ragged = canonicalize_table_structure(RAGGED)
        assert ragged.column_permutation == rect.column_permutation
        assert ragged.label_column == rect.label_column

    def test_raggedness_is_not_charged_to_the_model(self) -> None:
        # Same figures, read correctly; only the trailing cell is missing.
        # The digits present must score as read, not as a frame mismatch.
        score = score_document(RECTANGULAR, RAGGED, source="ragged-regression")
        assert score.numeric is not None
        assert score.numeric.value_exact_match > 0.5

    def test_colspans_are_expanded_rather_than_refused(self) -> None:
        """Superseded by canon 0.8.0; this asserted that colspans were refused.

        Refusing had the same asymmetry as refusing ragged rows -- it fired on
        the colspan-free ground truth and skipped the prediction -- so a span is
        now expanded into the grid positions it occupies instead.
        """
        spanned = (
            "<table>"
            "<tr><td colspan='2'>الموجودات المتداولة</td><td>٢٠٢٤ م</td></tr>"
            "<tr><td>٨٣٩</td><td>٨٦٦</td><td>نقد</td></tr>"
            "</table>"
        )
        out, report = canonicalize_table_structure(spanned)
        assert report.column_order_skipped is None
        assert report.expanded_spans == 1
        assert "colspan" not in out


class TestEmptyPredictionCannotRankAsAMeasurement:
    def test_status_is_forced_to_failed(self) -> None:
        score = score_document(RECTANGULAR, "   ", source="empty")
        assert score.empty_prediction is True
        row = from_document_score(score, system="s", document="d", status="api")
        assert row.status == "failed"

    def test_a_real_prediction_keeps_the_caller_s_status(self) -> None:
        score = score_document(RECTANGULAR, RECTANGULAR, source="real")
        row = from_document_score(score, system="s", document="d", status="api")
        assert row.status == "api"
