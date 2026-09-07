#!/usr/bin/env python3
"""Delete Windows ``Zone.Identifier`` alternate-data-stream leftovers from the repo.

Files copied out of WSL/Windows often carry a companion ``<name>:Zone.Identifier``
file. They are pure noise; this removes them.

Usage:
    python scripts/clean_zone_identifiers.py            # delete under repo root
    python scripts/clean_zone_identifiers.py --dry-run  # list only
    python scripts/clean_zone_identifiers.py path/to/dir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}


def find_zone_identifiers(root: Path) -> list[Path]:
    """Return every Zone.Identifier file under ``root``, skipping SKIP_DIRS."""
    matches: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and "Zone.Identifier" in path.name:
            matches.append(path)
    return sorted(matches)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=REPO_ROOT,
        type=Path,
        help="directory to clean (default: repo root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list what would be deleted without deleting",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1

    targets = find_zone_identifiers(root)
    if not targets:
        print("no Zone.Identifier files found")
        return 0

    deleted = 0
    for path in targets:
        rel = path.relative_to(root)
        if args.dry_run:
            print(f"would delete: {rel}")
            continue
        try:
            path.unlink()
        except OSError as exc:
            print(f"failed to delete {rel}: {exc}", file=sys.stderr)
        else:
            print(f"deleted: {rel}")
            deleted += 1

    if args.dry_run:
        print(f"{len(targets)} file(s) would be deleted")
    else:
        print(f"{deleted}/{len(targets)} file(s) deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
