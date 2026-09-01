"""Tests for tracked operator provenance declarations.

The unfairness this guards: a leaderboard row's operator-stated fields —
model version, mode, seed count — gate its admission, so they are part of the
row's proof of origin. Keeping them only beside the run output puts that proof
in untracked scratch, where `rm -rf output/` destroys it and no reader of the
repository can audit it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RUNS_DIR = Path(__file__).resolve().parents[2] / "arabicfinbench" / "runs"


def _declarations() -> list[Path]:
    return sorted(p for p in RUNS_DIR.glob("*.json"))


class TestTrackedDeclarations:
    def test_the_directory_is_tracked_and_populated(self) -> None:
        assert RUNS_DIR.is_dir()
        assert _declarations(), "no tracked run declarations"

    @pytest.mark.parametrize("path", _declarations(), ids=lambda p: p.stem)
    def test_each_declaration_parses_and_declares_a_model_version(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert payload.get("model_version"), f"{path.name} must state a model_version"

    @pytest.mark.parametrize("path", _declarations(), ids=lambda p: p.stem)
    def test_sampled_adapters_declare_at_least_three_seeds(self, path: Path) -> None:
        # The seed policy is enforced at admission too; declaring a sampled
        # adapter with one seed is a mistake worth catching at authoring time.
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("sampled"):
            assert payload.get("seed_count", 0) >= 3, f"{path.name}: sampled adapter needs >= 3 seeds"

    @pytest.mark.parametrize("path", _declarations(), ids=lambda p: p.stem)
    def test_declarations_name_a_registered_adapter(self, path: Path) -> None:
        from extract_bench.inference.pipelines import list_pipelines

        assert path.stem in set(list_pipelines()), f"{path.name} names an adapter not registered in this repository"


class TestDeclarationPrecedence:
    def test_underscore_keys_are_commentary_not_provenance(self, tmp_path: Path) -> None:
        # Declarations carry _mode_note-style commentary; it must never reach
        # the Provenance dataclass as a field.
        import sys

        sys.path.insert(0, str(RUNS_DIR.parents[1] / "scripts"))
        from afb_leaderboard import _operator_declaration

        tracked = tmp_path / "runs"
        tracked.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (tracked / "some_pipeline.json").write_text(
            json.dumps({"model_version": "v1", "_why": "commentary"}), encoding="utf-8"
        )

        import afb_leaderboard

        original = afb_leaderboard.RUNS_DIR
        afb_leaderboard.RUNS_DIR = tracked
        try:
            declaration = _operator_declaration("some_pipeline", out)
        finally:
            afb_leaderboard.RUNS_DIR = original

        assert declaration == {"model_version": "v1"}

    def test_a_local_file_overrides_the_tracked_one(self, tmp_path: Path) -> None:
        import sys

        sys.path.insert(0, str(RUNS_DIR.parents[1] / "scripts"))
        import afb_leaderboard
        from afb_leaderboard import _operator_declaration

        tracked = tmp_path / "runs"
        tracked.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (tracked / "p.json").write_text(json.dumps({"model_version": "tracked", "seed_count": 1}), encoding="utf-8")
        (out / "_afb_provenance.json").write_text(json.dumps({"model_version": "local"}), encoding="utf-8")

        original = afb_leaderboard.RUNS_DIR
        afb_leaderboard.RUNS_DIR = tracked
        try:
            declaration = _operator_declaration("p", out)
        finally:
            afb_leaderboard.RUNS_DIR = original

        # Local wins for the key it states; tracked survives for the rest.
        assert declaration == {"model_version": "local", "seed_count": 1}
