"""Tests for the structural canonicalisation of Arabic financial tables."""

from __future__ import annotations

from arabicfinbench.canon import strip_sections, strip_table_sections

# The same two rows of a balance sheet, encoded the two correct ways: the
# annotator's sparse row, and the parser's full-width span.
GT_TABLE = (
    "<table>"
    "<tr><th>٣١ ديسمبر ٢٠٢٣ م</th><th>٣١ ديسمبر ٢٠٢٤ م</th><th>إيضاح</th><th>الموجودات</th></tr>"
    "<tr><td></td><td></td><td></td><td>الموجودات المتداولة</td></tr>"
    "<tr><td>٨٣٩,٨٢١</td><td>٨٦٦,٠٨٣</td><td></td><td>نقد وأرصدة لدى البنوك</td></tr>"
    "</table>"
)

PRED_TABLE = (
    "<table>"
    "<tr><th>31 ديسمبر 2023م</th><th>31 ديسمبر 2024م</th><th>إيضاح</th><th>الموجودات</th></tr>"
    '<tr><th colspan="4">الموجودات المتداولة</th></tr>'
    "<tr><td>839,821</td><td>866,083</td><td></td><td>نقد وأرصدة لدى البنوك</td></tr>"
    "</table>"
)


class TestStripTableSections:
    def test_sparse_section_row_is_removed(self) -> None:
        out, report = strip_table_sections(GT_TABLE)
        assert report.rows_before == 3
        assert report.rows_after == 2
        assert report.sections_removed == 1
        assert "الموجودات المتداولة" not in out

    def test_full_width_colspan_row_is_removed(self) -> None:
        out, report = strip_table_sections(PRED_TABLE)
        assert report.rows_before == 3
        assert report.rows_after == 2
        assert report.sections_removed == 1
        assert "colspan" not in out

    def test_both_encodings_reduce_to_the_same_row_count(self) -> None:
        _, gt = strip_table_sections(GT_TABLE)
        _, pred = strip_table_sections(PRED_TABLE)
        assert gt.rows_after == pred.rows_after

    def test_the_section_label_is_recorded_not_discarded(self) -> None:
        _, report = strip_table_sections(GT_TABLE)
        assert report.sections[0].label == "الموجودات المتداولة"

    def test_both_encodings_record_the_same_section(self) -> None:
        _, gt = strip_table_sections(GT_TABLE)
        _, pred = strip_table_sections(PRED_TABLE)
        assert gt.sections[0].label == pred.sections[0].label
        assert gt.sections[0].before_row == pred.sections[0].before_row

    def test_before_row_indexes_the_section_free_grid(self) -> None:
        # Header is row 0; the section introduced what is now row 1.
        _, report = strip_table_sections(GT_TABLE)
        assert report.sections[0].before_row == 1

    def test_data_rows_survive_untouched(self) -> None:
        out, _ = strip_table_sections(GT_TABLE)
        assert "٨٣٩,٨٢١" in out
        assert "نقد وأرصدة لدى البنوك" in out

    def test_a_full_header_row_is_not_a_section(self) -> None:
        # Four non-empty cells: a header, not grouping context.
        out, report = strip_table_sections(GT_TABLE)
        assert report.sections_removed == 1
        assert "إيضاح" in out

    def test_a_table_of_only_sections_is_left_alone(self) -> None:
        # Reading every row as a section would delete the table; that is a
        # misapplication of the rule rather than a table without records.
        only = "<table><tr><td>الموجودات</td></tr><tr><td>المطلوبات</td></tr></table>"
        out, report = strip_table_sections(only)
        assert out == only
        assert report.sections_removed == 0
        assert report.rows_after == 2

    def test_a_table_without_sections_is_unchanged(self) -> None:
        plain = "<table><tr><td>١</td><td>٢</td></tr><tr><td>٣</td><td>٤</td></tr></table>"
        out, report = strip_table_sections(plain)
        assert out == plain
        assert report.sections_removed == 0

    def test_markup_outside_the_removed_rows_is_preserved(self) -> None:
        out, _ = strip_table_sections(PRED_TABLE)
        assert out.startswith("<table>")
        assert out.endswith("</table>")

    def test_an_empty_table_is_handled(self) -> None:
        out, report = strip_table_sections("<table></table>")
        assert out == "<table></table>"
        assert report.rows_before == 0
        assert report.rows_after == 0


class TestStripSections:
    def test_every_table_in_a_document_is_reported(self) -> None:
        doc = f"عنوان\n\n{GT_TABLE}\n\n{PRED_TABLE}"
        _, reports = strip_sections(doc)
        assert len(reports) == 2
        assert [r.sections_removed for r in reports] == [1, 1]

    def test_text_between_tables_is_preserved(self) -> None:
        doc = f"عنوان\n\n{GT_TABLE}\n\nخاتمة"
        out, _ = strip_sections(doc)
        assert "عنوان" in out
        assert "خاتمة" in out

    def test_a_document_without_tables_is_unchanged(self) -> None:
        out, reports = strip_sections("قائمة المركز المالي")
        assert out == "قائمة المركز المالي"
        assert reports == []

    def test_the_two_encodings_agree_after_stripping(self) -> None:
        # The whole point: differing section encodings stop shifting row
        # alignment once both sides are canonical.
        gt_out, _ = strip_sections(GT_TABLE)
        pred_out, _ = strip_sections(PRED_TABLE)
        gt_rows = gt_out.count("<tr")
        pred_rows = pred_out.count("<tr")
        assert gt_rows == pred_rows == 2


class TestBlankRows:
    """Blank spacer rows are not records and are not sections either."""

    BLANK = (
        "<table>"
        "<tr><td>٨٣٩,٨٢١</td><td>نقد وأرصدة لدى البنوك</td></tr>"
        "<tr><td></td><td></td></tr>"
        "<tr><td>٣,٧٨٠,٢٠٠</td><td>ذمم مدينة تجارية</td></tr>"
        "</table>"
    )

    def test_a_blank_row_is_removed(self) -> None:
        out, report = strip_table_sections(self.BLANK)
        assert report.rows_before == 3
        assert report.rows_after == 2
        assert report.blank_rows == 1

    def test_a_blank_row_is_not_counted_as_a_section(self) -> None:
        # It carries no label, so recording it as a section would invent one.
        _, report = strip_table_sections(self.BLANK)
        assert report.sections_removed == 0

    def test_data_rows_survive(self) -> None:
        out, _ = strip_table_sections(self.BLANK)
        assert "٨٣٩,٨٢١" in out
        assert "٣,٧٨٠,٢٠٠" in out

    def test_a_table_of_only_blanks_is_left_alone(self) -> None:
        only = "<table><tr><td></td></tr><tr><td></td></tr></table>"
        out, report = strip_table_sections(only)
        assert out == only
        assert report.blank_rows == 0

    def test_blanks_and_sections_are_counted_separately(self) -> None:
        mixed = (
            "<table>"
            '<tr><th colspan="2">الموجودات المتداولة</th></tr>'
            "<tr><td></td><td></td></tr>"
            "<tr><td>٨٣٩,٨٢١</td><td>نقد</td></tr>"
            "</table>"
        )
        _, report = strip_table_sections(mixed)
        assert report.sections_removed == 1
        assert report.blank_rows == 1
        assert report.rows_after == 1
