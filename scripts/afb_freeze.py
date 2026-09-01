#!/usr/bin/env python3
"""Freeze the test split: commit the sha256 of every test ground-truth file.

Run BEFORE any leaderboard run, and commit the output. The hashes are the
commitment: after this lands in the repository, an edit to any frozen file is
provable by anyone with the git history, and a leaderboard result scored
against drifted ground truth is detectable rather than deniable.

The freeze also refuses to run at all if the test split intersects the
training-exclusion manifest — contamination is checked at the moment of
commitment, not remembered later.

Usage::

    python scripts/afb_freeze.py                 # verify + write gt/freeze.json
    python scripts/afb_freeze.py --check         # verify an existing freeze
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from arabicfinbench.gt.contamination import (
    SplitManifest,
    build_freeze,
    check_training_exclusion,
    load_json,
    verify_freeze,
)

GT_DIR = Path("arabicfinbench/gt")


def _gt_files(manifest: SplitManifest) -> dict[str, Path]:
    """Ground-truth file per test document id; missing files are an error."""
    files: dict[str, Path] = {}
    missing: list[str] = []
    for doc_id in manifest.test:
        path = GT_DIR / f"{doc_id}.json"
        if path.exists():
            files[doc_id] = path
        else:
            missing.append(str(path))
    if missing:
        print(f"cannot freeze: test ground truth missing: {missing}", file=sys.stderr)
        raise SystemExit(1)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the existing freeze instead of writing one")
    args = ap.parse_args()

    manifest = SplitManifest.from_payload(load_json(GT_DIR / "splits.json"))
    check_training_exclusion(manifest, load_json(GT_DIR / "training_exclusion.json"))
    print(f"splits: {len(manifest.dev)} dev, {len(manifest.test)} test; exclusion check passed")

    freeze_path = GT_DIR / "freeze.json"
    files = _gt_files(manifest)

    if args.check:
        if not freeze_path.exists():
            print("no freeze.json to check", file=sys.stderr)
            return 1
        committed = json.loads(freeze_path.read_text(encoding="utf-8"))["hashes"]
        verify_freeze(committed, files)
        print(f"freeze verified: {len(committed)} file(s) byte-identical to the commitment")
        return 0

    if not manifest.test:
        print("nothing to freeze: the test split is empty (populate gt/splits.json first)")
        return 1

    payload = {
        "frozen_at": datetime.now(UTC).isoformat(),
        "hashes": build_freeze(files),
    }
    freeze_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {freeze_path}: {len(payload['hashes'])} commitment(s). Commit this before any leaderboard run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
