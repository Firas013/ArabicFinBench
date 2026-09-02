"""Tests for the scored-results store.

The unfairness this prevents: re-deriving every number on every read makes the
reported table depend on what the code happened to be doing that minute. A
result is a measurement — it belongs on disk, stamped with the canon version
that produced it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from arabicfinbench.results import (
    MixedCanonError,
    StoredScore,
    append,
    latest,
    load,
)


def _entry(system: str, *, canon: str = "0.4.0", trm_raw: float = 0.3, trm_struct: float = 0.9) -> StoredScore:
    return StoredScore(
        system=system,
        document="test_1/Test_1",
        canon_version=canon,
        scored_at="2026-09-02T10:00:00+00:00",
        passes={
            "raw": {"table_record_match": trm_raw},
            "text": {"table_record_match": (trm_raw + trm_struct) / 2},
            "struct": {"table_record_match": trm_struct},
        },
        coverage=0.99,
    )


class TestRoundTrip:
    def test_an_entry_survives_write_and_read(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a")], store=store)
        (loaded,) = load(store=store)
        assert loaded.system == "sys_a"
        assert loaded.passes["struct"]["table_record_match"] == pytest.approx(0.9)
        assert loaded.coverage == pytest.approx(0.99)

    def test_the_delta_is_derived_not_stored_wrong(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", trm_raw=0.32, trm_struct=0.91)], store=store)
        (loaded,) = load(store=store)
        assert loaded.raw_to_struct_delta == pytest.approx(0.59)

    def test_an_absent_store_reads_empty_rather_than_raising(self, tmp_path: Path) -> None:
        assert load(store=tmp_path / "nothing.jsonl") == []


class TestAppendOnly:
    def test_a_rescore_does_not_erase_the_previous_result(self, tmp_path: Path) -> None:
        # "Did this number move, and why" is only answerable if the old one survives.
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", trm_struct=0.80)], store=store)
        append([_entry("sys_a", trm_struct=0.91)], store=store)
        assert len(load(store=store)) == 2

    def test_the_newest_entry_wins_when_reading(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", trm_struct=0.80)], store=store)
        append([_entry("sys_a", trm_struct=0.91)], store=store)
        (current,) = latest(store=store)
        assert current.passes["struct"]["table_record_match"] == pytest.approx(0.91)

    def test_distinct_systems_both_survive(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a"), _entry("sys_b")], store=store)
        assert {e.system for e in latest(store=store)} == {"sys_a", "sys_b"}


class TestCanonVersionsAreNotMixed:
    def test_a_table_spanning_canon_versions_is_refused(self, tmp_path: Path) -> None:
        # Two results under different canon are not comparable; showing them
        # in one table silently is the error the stamp exists to prevent.
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", canon="0.3.0"), _entry("sys_b", canon="0.4.0")], store=store)
        with pytest.raises(MixedCanonError, match="0.3.0"):
            latest(store=store)

    def test_pinning_a_version_selects_cleanly(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", canon="0.3.0"), _entry("sys_b", canon="0.4.0")], store=store)
        selected = latest(canon_version="0.4.0", store=store)
        assert [e.system for e in selected] == ["sys_b"]

    def test_one_system_rescored_under_a_new_canon_keeps_both(self, tmp_path: Path) -> None:
        store = tmp_path / "scores.jsonl"
        append([_entry("sys_a", canon="0.3.0", trm_struct=0.56)], store=store)
        append([_entry("sys_a", canon="0.4.0", trm_struct=0.91)], store=store)
        old = latest(canon_version="0.3.0", store=store)
        new = latest(canon_version="0.4.0", store=store)
        assert old[0].passes["struct"]["table_record_match"] == pytest.approx(0.56)
        assert new[0].passes["struct"]["table_record_match"] == pytest.approx(0.91)


class TestTheCommittedStore:
    def test_the_repository_store_reads_and_is_single_canon(self) -> None:
        from arabicfinbench.canon.version import CANON_VERSION

        store = Path(__file__).resolve().parents[2] / "results" / "scores.jsonl"
        if not store.exists():
            pytest.skip("no results recorded yet")
        entries = latest(document="test_1/Test_1", canon_version=CANON_VERSION, store=store)
        assert entries, "no entries at the current canon version; re-record"
        assert all(e.canon_version == CANON_VERSION for e in entries)
