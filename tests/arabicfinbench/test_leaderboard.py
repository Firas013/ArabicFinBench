"""Tests for the leaderboard generator's refusals.

Guards 4, 6, 9, 10. Each test names the unfairness it prevents:

- a row that cannot prove its origin becomes a citable rumour (provenance);
- a hand-imported run has guessed mode/cost/latency columns (one path);
- an adapter whose code is not public is not reproducible (inclusion);
- a sampled model's lucky single run beside a deterministic run misleads
  (seed policy);
- one combined number ranks confident wrong figures above honest imperfect
  ones (never one number).
"""

from __future__ import annotations

import pytest

from arabicfinbench.determinism import (
    DeterminismClass,
    SeedPolicyError,
    check_seed_count,
    declare,
    verify,
)
from arabicfinbench.leaderboard import (
    REFERENCE_LABEL,
    CombinedScoreError,
    LeaderboardRow,
    UnknownAdapterError,
    build_dev_report,
    build_leaderboard,
    validate_row,
)
from arabicfinbench.provenance import (
    NO_PROMPT,
    HandImportedResultError,
    MissingProvenanceError,
    Provenance,
)
from arabicfinbench.scoring import DocumentScore, SideTrace

_TRACE = SideTrace(text_rules=(), structure_rules=(), tables=())


def _score(raw: float, struct: float, fidelity: float | None = 1.0) -> DocumentScore:
    return DocumentScore(
        passes={
            "raw": {"table_record_match": raw},
            "text": {"table_record_match": (raw + struct) / 2},
            "struct": {"table_record_match": struct},
        },
        gt_trace=_TRACE,
        pred_trace=_TRACE,
        script_fidelity=fidelity,
    )


def _full_provenance(**overrides) -> Provenance:
    base = {
        "adapter": "llamaparse_agentic",  # registered in the public repo
        "model_version": "llamaparse/agentic@latest",
        "mode": "agentic",
        "canon_version": "0.3.0",
        "cost_per_page_usd": 0.0125,
        "median_latency_ms": 12633.0,
        "seed_count": 1,
        "run_timestamp": "2026-09-01T16:00:00+03:00",
        "page_image_hashes": ("a" * 64, "b" * 64, "c" * 64),
        "prompt_sha256": NO_PROMPT,
    }
    base.update(overrides)
    return Provenance(**base)


def _row(**overrides) -> LeaderboardRow:
    return LeaderboardRow(
        provenance=_full_provenance(**overrides),
        scores={"test_1/Test_1": _score(0.32, 0.91, 0.24)},
    )


class TestProvenanceIsRequired:
    @pytest.mark.parametrize(
        "field,empty",
        [
            ("model_version", ""),
            ("mode", ""),
            ("canon_version", ""),
            ("cost_per_page_usd", None),
            ("median_latency_ms", None),
            ("seed_count", None),
            ("run_timestamp", ""),
            ("page_image_hashes", ()),
            ("prompt_sha256", ""),
        ],
    )
    def test_each_missing_field_rejects_the_row_by_name(self, field: str, empty) -> None:
        row = _row(**{field: empty})
        with pytest.raises(MissingProvenanceError) as excinfo:
            validate_row(row)
        assert field in str(excinfo.value)

    def test_a_complete_row_is_admitted(self) -> None:
        validate_row(_row())  # should not raise

    def test_multiple_missing_fields_are_all_named(self) -> None:
        row = _row(mode="", run_timestamp="")
        with pytest.raises(MissingProvenanceError) as excinfo:
            validate_row(row)
        assert "mode" in str(excinfo.value)
        assert "run_timestamp" in str(excinfo.value)

    def test_prompt_free_adapters_state_none_rather_than_omit(self) -> None:
        # "none" is an explicit statement and passes; "" is an omission.
        validate_row(_row(prompt_sha256=NO_PROMPT))
        with pytest.raises(MissingProvenanceError, match="prompt_sha256"):
            validate_row(_row(prompt_sha256=""))


class TestHandImportsAreDevOnly:
    def test_a_hand_imported_row_is_blocked_from_the_leaderboard(self) -> None:
        with pytest.raises(HandImportedResultError, match="dev report"):
            validate_row(_row(hand_imported=True))

    def test_the_same_row_is_welcome_in_the_dev_report(self) -> None:
        report = build_dev_report([_row(hand_imported=True)], metrics=("table_record_match",))
        assert "hand-imported (dev only)" in report


class TestAdapterMustBePublic:
    def test_an_unregistered_adapter_is_rejected(self) -> None:
        row = _row(adapter="secret_internal_pipeline")
        with pytest.raises(UnknownAdapterError, match="secret_internal_pipeline"):
            validate_row(row)


class TestSeedPolicy:
    def test_nondeterministic_adapter_with_one_seed_is_rejected(self) -> None:
        policy = declare("some_vlm", sampled=True)
        with pytest.raises(SeedPolicyError, match="requires 3"):
            check_seed_count(policy, 1)

    def test_nondeterministic_adapter_with_three_seeds_passes(self) -> None:
        policy = declare("some_vlm", sampled=True)
        check_seed_count(policy, 3)  # should not raise

    def test_deterministic_adapter_runs_once_and_says_so(self) -> None:
        policy = declare("an_api", sampled=False)
        check_seed_count(policy, 1)
        assert "runs once" in policy.report_note

    def test_double_run_verification_upgrades_or_flags(self) -> None:
        stable = verify("stable_adapter", lambda: "same output")
        assert stable.determinism is DeterminismClass.VERIFIED
        assert stable.required_seeds == 1

        outputs = iter(["one", "two"])
        flaky = verify("flaky_adapter", lambda: next(outputs))
        assert flaky.determinism is DeterminismClass.NONDETERMINISTIC
        assert flaky.required_seeds == 3

    def test_a_row_for_a_flagged_adapter_needs_three_seeds(self) -> None:
        outputs = iter(["one", "two"])
        policy = verify("flaky_adapter2", lambda: next(outputs))
        row = LeaderboardRow(
            provenance=_full_provenance(seed_count=1),
            scores={"t": _score(0.5, 0.6)},
            determinism=policy,
        )
        with pytest.raises(SeedPolicyError):
            validate_row(row)


class TestNeverOneNumber:
    def test_asking_for_a_combined_score_raises(self) -> None:
        with pytest.raises(CombinedScoreError, match="one number|combined"):
            build_leaderboard([_row()], metrics=("table_record_match",), combined=True)

    def test_an_overall_column_raises(self) -> None:
        with pytest.raises(CombinedScoreError, match="overall"):
            build_leaderboard([_row()], metrics=("overall",))

    def test_emitted_tables_contain_no_overall_column(self) -> None:
        table = build_leaderboard([_row()], metrics=("table_record_match",))
        assert "overall" not in table.lower()


class TestRawNextToCanonAlways:
    def test_every_table_shows_all_passes_and_the_delta(self) -> None:
        table = build_leaderboard([_row()], metrics=("table_record_match",))
        for column in ("raw", "text", "struct", "raw→struct Δ", "script fidelity"):
            assert column in table

    def test_the_delta_is_the_convention_diagnostic(self) -> None:
        table = build_leaderboard([_row()], metrics=("table_record_match",))
        assert "+0.5900" in table  # 0.91 - 0.32, the Test_1-shaped movement


class TestReferenceLabelling:
    def test_the_reference_implementation_is_labelled_on_its_rows(self) -> None:
        table = build_leaderboard([_row(reference_implementation=True)], metrics=("table_record_match",))
        assert REFERENCE_LABEL in table

    def test_ordinary_rows_carry_no_label(self) -> None:
        table = build_leaderboard([_row()], metrics=("table_record_match",))
        assert REFERENCE_LABEL not in table
