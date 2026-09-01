"""Tests for ground-truth integrity and contamination controls.

Guards 7 and 8. The unfairness pinned: a benchmark whose ground truth is
malformed, arithmetically wrong, quietly edited, or drawn from its authors'
own training data is scoring something — just not the models.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from arabicfinbench.gt import (
    AdmissionError,
    GTSchemaError,
    Relation,
    admit_page,
    consensus_flags,
    parse_amount,
    validate_gt_schema,
)
from arabicfinbench.gt.contamination import (
    ContaminationError,
    FreezeViolationError,
    SplitManifest,
    SplitManifestError,
    build_freeze,
    check_training_exclusion,
    verify_freeze,
)

# A minimal balance-sheet fragment whose totals actually reconcile:
# 839,821 + 24,061,612 = 24,901,433 (current); + 11,575,509 = 36,476,942.
GOOD_PAGE = {
    "lines": [{"text": "قائمة المركز المالي"}],
    "tables": [
        {
            "rows": [
                ["إيضاح", "٢٠٢٤ م", "البند"],
                ["", "٨٣٩,٨٢١", "نقد وأرصدة لدى البنوك"],
                ["", "٢٤,٠٦١,٦١٢", "المخزون"],
                ["", "٢٤,٩٠١,٤٣٣", "إجمالي الموجودات المتداولة"],
                ["٨", "١١,٥٧٥,٥٠٩", "ممتلكات ومعدات"],
                ["", "٣٦,٤٧٦,٩٤٢", "إجمالي الموجودات"],
            ]
        }
    ],
}

RELATIONS = [
    Relation(name="current_assets", table=0, total=(3, 1), addends=((1, 1), (2, 1))),
    Relation(name="total_assets", table=0, total=(5, 1), addends=((3, 1), (4, 1))),
]


class TestSchemaValidation:
    def test_a_valid_page_passes(self) -> None:
        validate_gt_schema(GOOD_PAGE)

    def test_defects_are_named_not_just_counted(self) -> None:
        bad = {"lines": [{"no_text": 1}], "tables": [{"rows": [["ا"], ["ب", "ج"]]}]}
        with pytest.raises(GTSchemaError) as excinfo:
            validate_gt_schema(bad, source="page-9")
        message = str(excinfo.value)
        assert "page-9" in message
        assert "lines[0]" in message
        assert "ragged" in message

    def test_blank_spacer_rows_violate_conventions(self) -> None:
        # CONVENTIONS.md §3: parsers emit spacer rows, ground truth must not.
        bad = {"lines": [], "tables": [{"rows": [["نقد", "٥"], ["", ""]]}]}
        with pytest.raises(GTSchemaError, match="blank"):
            validate_gt_schema(bad)

    def test_non_dict_pages_are_refused(self) -> None:
        with pytest.raises(GTSchemaError, match="top level"):
            validate_gt_schema(["not", "a", "page"])


class TestAmountParsing:
    def test_thousands_grouping_in_either_script(self) -> None:
        assert parse_amount("٢٤,٠٦١,٦١٢") == 24_061_612
        assert parse_amount("24,061,612") == 24_061_612

    def test_accounting_negative_parses_negative(self) -> None:
        assert parse_amount("(٤١٥,٦٥٩)") == -415_659

    def test_decimal_comma_is_a_decimal_not_thousands(self) -> None:
        # The zakat rate ٠,٠٢٥٨ must not silently become 258.
        assert parse_amount("٠,٠٢٥٨") == Fraction(258, 10_000)

    def test_dash_is_nil(self) -> None:
        assert parse_amount("-") == 0

    def test_the_ambiguous_is_refused_not_guessed(self) -> None:
        from arabicfinbench.gt.integrity import AmountParseError

        with pytest.raises(AmountParseError, match="cannot read"):
            # A 4-digit head with a 3-digit tail is neither thousands grouping
            # nor a decimal comma; guessing either way could be off by 1000x.
            parse_amount("١٢٣٤,٥٦٧")


class TestAdmissionGate:
    def test_a_reconciling_page_is_admitted(self) -> None:
        report = admit_page(GOOD_PAGE, RELATIONS)
        assert len(report.results) == 2
        assert not report.failures

    def test_a_page_with_no_relations_is_not_admitted(self) -> None:
        # An unchecked page is an unearned assumption, not a lenient default.
        with pytest.raises(AdmissionError, match="no arithmetic relations"):
            admit_page(GOOD_PAGE, [])

    def test_a_failing_relation_rejects_the_page_with_both_values(self) -> None:
        broken = {
            "lines": [],
            "tables": [{"rows": [["٥٠٠", "أ"], ["٣٠٠", "ب"], ["١٠٠", "ج"]]}],
        }
        rel = Relation(name="broken_total", table=0, total=(0, 0), addends=((1, 0), (2, 0)))
        with pytest.raises(AdmissionError) as excinfo:
            admit_page(broken, [rel])
        message = str(excinfo.value)
        assert "broken_total" in message
        assert "500" in message and "400" in message  # stated and computed, both named

    def test_arithmetic_blind_cells_get_their_own_line(self) -> None:
        report = admit_page(GOOD_PAGE, RELATIONS, arithmetic_blind=["t0.r0.c0: note reference"])
        assert report.arithmetic_blind == ("t0.r0.c0: note reference",)

    def test_a_relation_addressing_a_missing_cell_is_an_error_not_a_pass(self) -> None:
        rel = Relation(name="off_grid", table=0, total=(99, 0), addends=((1, 1),))
        with pytest.raises(AdmissionError, match="off_grid"):
            admit_page(GOOD_PAGE, [rel])


class TestConsensusAgainstGT:
    GT = [[["٧/١", "المستحق"]]]

    def test_two_agreeing_systems_flag_the_cell(self) -> None:
        systems = {
            "model_a": [[["٧/أ", "المستحق"]]],
            "model_b": [[["7/أ", "المستحق"]]],  # same value, other script — canon agrees
        }
        flags = consensus_flags(self.GT, systems)
        assert len(flags) == 1
        flag = flags[0]
        assert (flag.table, flag.row, flag.col) == (0, 0, 0)
        assert flag.gt_value == "7/1"
        assert flag.consensus_value == "7/أ"
        assert flag.agreeing_systems == ("model_a", "model_b")

    def test_one_dissenting_system_is_not_consensus(self) -> None:
        systems = {
            "model_a": [[["٧/أ", "المستحق"]]],
            "model_b": [[["٧/١", "المستحق"]]],  # agrees with GT
        }
        assert consensus_flags(self.GT, systems) == []

    def test_systems_that_cannot_address_the_cell_do_not_vote(self) -> None:
        systems = {
            "model_a": [[["٧/أ", "المستحق"]]],
            "model_b": [[]],  # segmented differently; no cell to compare
        }
        assert consensus_flags(self.GT, systems) == []


class TestSplitManifest:
    def test_overlapping_splits_are_refused(self) -> None:
        with pytest.raises(SplitManifestError, match="both dev and test"):
            SplitManifest.from_payload({"dev": ["doc1"], "test": ["doc1"]})

    def test_the_committed_manifests_parse_and_validate(self) -> None:
        from arabicfinbench.gt.contamination import load_json

        root = Path(__file__).resolve().parents[2] / "arabicfinbench" / "gt"
        manifest = SplitManifest.from_payload(load_json(root / "splits.json"))
        check_training_exclusion(manifest, load_json(root / "training_exclusion.json"))


class TestTrainingExclusion:
    def test_a_contaminated_test_document_fails_the_build(self) -> None:
        splits = SplitManifest.from_payload({"dev": [], "test": ["tadawul_0001"]})
        exclusion = {"documents": [{"id": "tadawul_0001", "sha256": "f" * 64, "source": "rec v9"}]}
        with pytest.raises(ContaminationError, match="tadawul_0001"):
            check_training_exclusion(splits, exclusion)

    def test_a_clean_test_split_passes(self) -> None:
        splits = SplitManifest.from_payload({"dev": ["d1"], "test": ["t1"]})
        exclusion = {"documents": [{"id": "d1", "sha256": "a" * 64}]}  # dev overlap is fine
        check_training_exclusion(splits, exclusion)


class TestFreeze:
    def test_the_commitment_detects_a_post_freeze_edit(self, tmp_path: Path) -> None:
        gt = tmp_path / "doc1.json"
        gt.write_text('{"lines": [], "tables": []}', encoding="utf-8")
        freeze = build_freeze({"doc1": gt})

        verify_freeze(freeze, {"doc1": gt})  # untouched: passes

        gt.write_text('{"lines": [], "tables": [], "edited": true}', encoding="utf-8")
        with pytest.raises(FreezeViolationError, match="doc1"):
            verify_freeze(freeze, {"doc1": gt})

    def test_a_missing_frozen_file_is_a_violation_not_a_skip(self, tmp_path: Path) -> None:
        gt = tmp_path / "doc1.json"
        gt.write_text("{}", encoding="utf-8")
        freeze = build_freeze({"doc1": gt})
        gt.unlink()
        with pytest.raises(FreezeViolationError, match="missing"):
            verify_freeze(freeze, {"doc1": gt})
