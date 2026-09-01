"""Contamination controls: splits, the freeze commitment, training exclusion.

The unfairness these guard: a model scored on pages it trained on, or a
ground truth quietly edited after the leaderboard ran. Three mechanisms:

Split manifest (``gt/splits.json``)
    dev: images and ground truth public. test: images public, ground truth
    withheld. The manifest is data with a validator, not a convention.

Freeze commitment (``gt/freeze.json``, written by ``scripts/afb_freeze.py``)
    On freeze, the sha256 of every test-split ground-truth file is committed
    to the repository BEFORE any leaderboard run. The hashes are the
    commitment: a later edit to a frozen file is provable by anyone with the
    repo history.

Training-exclusion manifest (``gt/training_exclusion.json``)
    Every document that has ever touched any of our own training sets, by
    content hash. The test split is built from documents NOT in it, checked
    by code here and reported in the paper — the check is the claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SplitManifestError(ValueError):
    """The split manifest is malformed or self-contradictory."""


class ContaminationError(ValueError):
    """A test-split document appears in the training-exclusion manifest."""


class FreezeViolationError(ValueError):
    """A frozen ground-truth file no longer matches its committed hash."""


@dataclass(frozen=True)
class SplitManifest:
    dev: tuple[str, ...] = field(default_factory=tuple)
    test: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_payload(cls, payload: Any) -> SplitManifest:
        if not isinstance(payload, dict):
            raise SplitManifestError(f"split manifest must be an object, got {type(payload).__name__}")
        dev = payload.get("dev", [])
        test = payload.get("test", [])
        for name, ids in (("dev", dev), ("test", test)):
            if not isinstance(ids, list) or not all(isinstance(i, str) and i for i in ids):
                raise SplitManifestError(f"'{name}' must be a list of non-empty document ids")
        overlap = set(dev) & set(test)
        if overlap:
            raise SplitManifestError(f"documents in both dev and test: {sorted(overlap)}")
        return cls(dev=tuple(dev), test=tuple(test))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_freeze(gt_files: dict[str, Path]) -> dict[str, str]:
    """The commitment: document id -> sha256 of its ground-truth file."""
    return {doc_id: sha256_file(path) for doc_id, path in sorted(gt_files.items())}


def verify_freeze(freeze: dict[str, str], gt_files: dict[str, Path]) -> None:
    """Prove the frozen ground truth is byte-identical to the commitment.

    :raises FreezeViolationError: naming every drifted or missing file.
    """
    problems: list[str] = []
    for doc_id, committed in sorted(freeze.items()):
        path = gt_files.get(doc_id)
        if path is None or not path.exists():
            problems.append(f"{doc_id}: frozen file missing")
            continue
        actual = sha256_file(path)
        if actual != committed:
            problems.append(f"{doc_id}: hash {actual[:12]}… != committed {committed[:12]}…")
    if problems:
        raise FreezeViolationError("frozen ground truth drifted: " + "; ".join(problems))


def check_training_exclusion(splits: SplitManifest, exclusion_payload: Any) -> None:
    """Refuse a test split that intersects our own training history.

    The exclusion manifest lists, by document id and content hash, every
    document that has ever touched any of our training sets. Its
    ``documents`` list being complete is an obligation on the benchmark
    authors; this check turns that obligation into a failing build instead of
    a footnote.

    :raises ContaminationError: naming every contaminated test document.
    """
    if not isinstance(exclusion_payload, dict) or not isinstance(exclusion_payload.get("documents"), list):
        raise SplitManifestError("training-exclusion manifest must be an object with a 'documents' list")
    excluded_ids = set()
    for entry in exclusion_payload["documents"]:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise SplitManifestError(f"exclusion entry must be an object with an 'id': {entry!r}")
        excluded_ids.add(entry["id"])
    contaminated = sorted(set(splits.test) & excluded_ids)
    if contaminated:
        raise ContaminationError(
            "test-split document(s) appear in the training-exclusion manifest "
            f"(they touched our training sets): {contaminated}"
        )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
