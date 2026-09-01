"""Tests for canonical column ordering — the direction-of-reading guard.

The unfairness this pins down: an RTL page yields a label-first array from one
faithful reader and label-last from another, and on Test_1 the ground truth
itself disagreed table-to-table (table 0 label-last, tables 2–4 reversed).
Positional agreement swung 98% → 0% between tables whose content matched.
Without this guard, a system is scored on whether its reading direction
happened to match the annotator's mood on that table.
"""

from __future__ import annotations

from arabicfinbench.canon import (
    canonical_column_order,
    canonicalize_structure,
    canonicalize_table_structure,
)
from arabicfinbench.canon.structure import _cells  # noqa: PLC2701 - test peers into parsing


def _grid(table_html: str) -> list[list[str]]:
    import re

    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", table_html, re.S)
    return [[c.text for c in _cells(r)] for r in rows]


# The same two records, rendered with every convention flipped: label side,
# digit script, section encoding, spacer rows, and year order.
GT_LABEL_LAST = (
    "<table>"
    "<tr><th>٣١ ديسمبر ٢٠٢٣ م</th><th>٣١ ديسمبر ٢٠٢٤ م</th><th>إيضاح</th><th>الموجودات</th></tr>"
    "<tr><td></td><td></td><td></td><td>الموجودات المتداولة</td></tr>"
    "<tr><td>٨٣٩</td><td>٨٦٦</td><td></td><td>نقد وأرصدة</td></tr>"
    "<tr><td>(٤١٥)</td><td>(١٩٧)</td><td>٥</td><td>فوائد مؤجلة</td></tr>"
    "</table>"
)

PRED_LABEL_FIRST = (
    "<table>"
    "<tr><th>الموجودات</th><th>إيضاح</th><th>31 ديسمبر 2024م</th><th>31 ديسمبر 2023م</th></tr>"
    '<tr><th colspan="4">الموجودات المتداولة</th></tr>'
    "<tr><td></td><td></td><td></td><td></td></tr>"
    "<tr><td>نقد وأرصدة</td><td></td><td>866</td><td>839</td></tr>"
    "<tr><td>فوائد مؤجلة</td><td>5</td><td>(197)</td><td>(415)</td></tr>"
    "</table>"
)


class TestCanonicalColumnOrder:
    def test_label_column_is_found_from_bodies_not_headers(self) -> None:
        # The label header is empty — exactly the Test_1 t1 case — so a
        # header-based rule would misfire. Bodies decide.
        rows = [
            list(_cells("<tr><th>2023</th><th>2024</th><th></th></tr>")),
            list(_cells("<tr><td>100</td><td>200</td><td>رأس المال</td></tr>")),
            list(_cells("<tr><td>300</td><td>400</td><td>أرباح مبقاة</td></tr>")),
        ]
        order = canonical_column_order(rows)
        assert order is not None
        assert order[0] == 2  # the text column leads, despite its blank header

    def test_dated_columns_sort_ascending_by_parsed_date(self) -> None:
        rows = [
            list(_cells("<tr><th>٣١ ديسمبر ٢٠٢٤ م</th><th>٣١ ديسمبر ٢٠٢٣ م</th><th>بيان</th></tr>")),
            list(_cells("<tr><td>866</td><td>839</td><td>نقد</td></tr>")),
        ]
        order = canonical_column_order(rows)
        assert order == (2, 1, 0)  # label, then 2023 before 2024

    def test_a_note_column_keeps_its_place_between_label_and_dates(self) -> None:
        rows = [
            list(_cells("<tr><th>٢٠٢٣ م</th><th>٢٠٢٤ م</th><th>إيضاح</th><th>الموجودات</th></tr>")),
            list(_cells("<tr><td>1</td><td>2</td><td>5</td><td>نقد</td></tr>")),
        ]
        order = canonical_column_order(rows)
        assert order == (3, 2, 0, 1)


class TestOppositeConventionsConverge:
    def test_both_renderings_canonicalize_to_the_same_grid(self) -> None:
        gt_out, _ = canonicalize_table_structure(GT_LABEL_LAST)
        pred_out, _ = canonicalize_table_structure(PRED_LABEL_FIRST)
        # Content equality is what matters; compare parsed grids after text
        # canon (structure canon canonicalises cell text for its own analysis,
        # but preserves original cell markup — so canonicalize both grids).
        from arabicfinbench.canon import canonicalize

        gt_grid = [[canonicalize(c) for c in row] for row in _grid(gt_out)]
        pred_grid = [[canonicalize(c) for c in row] for row in _grid(pred_out)]
        assert gt_grid == pred_grid

    def test_the_permutation_is_recorded_not_silent(self) -> None:
        _, report = canonicalize_table_structure(GT_LABEL_LAST)
        assert report.column_permutation is not None
        assert report.label_column == report.column_permutation[0]
        assert report.columns_reordered

    def test_identity_permutation_is_not_reported_as_reordering(self) -> None:
        already_canonical = (
            "<table>"
            "<tr><th>الموجودات</th><th>إيضاح</th><th>٢٠٢٣ م</th><th>٢٠٢٤ م</th></tr>"
            "<tr><td>نقد</td><td>٥</td><td>٨٣٩</td><td>٨٦٦</td></tr>"
            "</table>"
        )
        out, report = canonicalize_table_structure(already_canonical)
        assert out == already_canonical
        assert not report.columns_reordered


class TestColumnOrderRefusesToGuess:
    def test_ragged_tables_are_skipped_with_a_named_reason(self) -> None:
        ragged = (
            "<table>"
            "<tr><td>ا</td><td>ب</td><td>ج</td></tr>"
            "<tr><td>١</td><td>٢</td></tr>"
            "<tr><td>٣</td><td>٤</td><td>٥</td></tr>"
            "</table>"
        )
        out, report = canonicalize_table_structure(ragged)
        assert out == ragged
        assert report.column_order_skipped == "ragged"

    def test_residual_colspans_are_skipped_with_a_named_reason(self) -> None:
        # A colspan that is not a section (two non-empty cells) survives the
        # section strip; permuting around it would corrupt the grid.
        spanned = (
            "<table>"
            '<tr><td colspan="2">أ ب</td><td>ج</td><td>د</td></tr>'
            "<tr><td>١</td><td>٢</td><td>هـ</td></tr>"
            "<tr><td>٣</td><td>٤</td><td>و</td></tr>"
            "</table>"
        )
        out, report = canonicalize_table_structure(spanned)
        assert out == spanned
        assert report.column_order_skipped == "colspan"


class TestStructureFiringNames:
    def test_fired_rules_are_named_per_document(self) -> None:
        _, _, fired = canonicalize_structure(PRED_LABEL_FIRST)
        assert "structure/sections" in fired
        assert "structure/blank_rows" in fired
        assert "structure/column_order" in fired

    def test_a_canonical_document_fires_nothing(self) -> None:
        already = "<table><tr><td>نقد</td><td>٨٣٩</td></tr><tr><td>مخزون</td><td>٢٤</td></tr></table>"
        _, _, fired = canonicalize_structure(already)
        assert fired == ()
