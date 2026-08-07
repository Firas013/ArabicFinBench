"""Download the ExtractBench dataset from HuggingFace.

Dataset: https://huggingface.co/datasets/llamaindex/ExtractBench

The hub stores one JSONL row per (document, schema) test case plus the source
documents under ``docs/<split>/``. After download, each row is reconstructed
into the sidecar layout the test-case loader consumes natively:

    <local_dir>/
    ├── short/<stem>.pdf + <stem>.test.json
    ├── medium/<stem>.pdf + <stem>.test.json
    └── long/<stem>.pdf + <stem>.test.json

Row columns ``data_schema`` / ``expected_output`` / ``field_rules`` /
``repeated_structure`` are JSON-encoded strings (schemas differ per document).
``field_rules`` holds either the ``_field_rules`` dict shape or the
``test_rules`` list shape; it is written back to the matching sidecar key
based on its JSON type.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

DATASET_REPO = "llamaindex/ExtractBench"
DATASET_REPO_TYPE = "dataset"
TEST_DATA_REVISION = "test-data"

SPLITS = ["short", "medium", "long"]

# Default on-disk locations. Test data lives in a sibling subdirectory so the
# two datasets coexist and `--test` does not silently overlay or get masked
# by an existing full download.
DEFAULT_DATA_DIR = Path("./data")
DEFAULT_TEST_DATA_DIR = Path("./data/test")

# Written after a fully successful reconstruction; records the resolved HF
# revision and per-split case counts so `is_dataset_ready` can distinguish a
# complete download from an interrupted one.
MANIFEST_NAME = ".extract_bench_manifest.json"


def default_data_dir(test: bool = False) -> Path:
    """Return the default on-disk dataset path for the given mode.

    Used by every CLI surface that takes ``--test`` so the routing is
    consistent between ``download``, ``run`` and ``status``.
    """
    return DEFAULT_TEST_DATA_DIR if test else DEFAULT_DATA_DIR


def read_manifest(data_dir: Path) -> dict | None:
    """Return the download manifest for ``data_dir``, or None if absent/invalid."""
    manifest_path = data_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return manifest if isinstance(manifest, dict) else None


def is_dataset_ready(data_dir: Path) -> bool:
    """True when the manifest exists and every split has all recorded sidecars.

    An interrupted reconstruction leaves no manifest (it is written last), so
    partial downloads report not-ready and get repaired by the next download.
    """
    if not data_dir.exists():
        return False
    manifest = read_manifest(data_dir)
    if manifest is None:
        return False
    per_split = manifest.get("per_split")
    if not isinstance(per_split, dict):
        return False
    for split in SPLITS:
        split_dir = data_dir / split
        expected = per_split.get(split)
        if not isinstance(expected, int):
            return False
        if not split_dir.exists() or sum(1 for _ in split_dir.rglob("*.test.json")) < expected:
            return False
    return True


def _remote_revision(revision: str | None) -> str | None:
    """Resolve ``revision`` to a commit sha, or None when the Hub is unreachable."""
    try:
        from huggingface_hub import HfApi

        return HfApi().repo_info(DATASET_REPO, repo_type=DATASET_REPO_TYPE, revision=revision).sha
    except Exception:
        return None


def _revision_is_stale(data_dir: Path, revision: str | None) -> bool:
    """True when the Hub has moved past the commit recorded in the manifest.

    Case counts alone cannot detect this: a branch can swap which documents it
    ships while keeping the same number per split. Offline, the answer is False
    so an existing download stays usable.
    """
    manifest = read_manifest(data_dir)
    local = (manifest or {}).get("revision")
    if not isinstance(local, str):
        return False
    remote = _remote_revision(revision)
    return remote is not None and remote != local


def _prune_orphans(data_dir: Path, keep: set[Path]) -> list[Path]:
    """Delete reconstructed sidecars (and their PDFs) no longer in the dataset."""
    removed = []
    for split in SPLITS:
        split_dir = data_dir / split
        if not split_dir.is_dir():
            continue
        for sidecar in sorted(split_dir.rglob("*.test.json")):
            if sidecar in keep:
                continue
            pdf = sidecar.with_name(sidecar.name[: -len(".test.json")] + ".pdf")
            sidecar.unlink()
            removed.append(sidecar)
            if pdf.exists():
                pdf.unlink()
    return removed


def _write_sidecar(row: dict, split_dir: Path, snapshot_dir: Path, force: bool = False) -> Path:
    """Reconstruct one JSONL row into ``<stem>.pdf`` + ``<stem>.test.json``.

    Returns the sidecar path written.
    """
    pdf_rel = row["pdf"]  # e.g. docs/short/<stem>.pdf
    # The path comes from repo data — never let it escape the target dirs.
    pdf_rel_parts = Path(pdf_rel).parts
    if Path(pdf_rel).is_absolute() or ".." in pdf_rel_parts or not pdf_rel.startswith("docs/"):
        raise RuntimeError(f"Dataset row {row.get('id')} has an unsafe file path: {pdf_rel!r}")
    src_pdf = snapshot_dir / pdf_rel
    if not src_pdf.exists():
        raise FileNotFoundError(f"Dataset row {row.get('id')} references missing file: {pdf_rel}")

    stem = Path(pdf_rel).stem
    # Preserve any sub-group directories below docs/<split>/.
    rel_parent = Path(pdf_rel).parent.relative_to(Path("docs") / row["category"])
    dest_dir = split_dir / rel_parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_pdf = dest_dir / f"{stem}.pdf"
    if force or not dest_pdf.exists():
        shutil.copyfile(src_pdf, dest_pdf)

    sidecar: dict = {
        "tags": row.get("tags") or [],
        "data_schema": json.loads(row["data_schema"]),
        "expected_output": json.loads(row["expected_output"]),
    }
    rules = json.loads(row.get("field_rules") or "{}")
    if isinstance(rules, dict) and rules:
        sidecar["_field_rules"] = rules
    elif isinstance(rules, list) and rules:
        sidecar["test_rules"] = rules
    # The loader only reads `_eval_row_identity`; `_repeated_structure` is an
    # inert legacy key, so landing the column there would leave row identity
    # dormant for every consumer.
    repeated = json.loads(row.get("repeated_structure") or "{}")
    if repeated:
        sidecar["_eval_row_identity"] = repeated

    dest_sidecar = dest_dir / f"{stem}.test.json"
    dest_sidecar.write_text(json.dumps(sidecar, ensure_ascii=False), encoding="utf-8")
    return dest_sidecar


def download_dataset(
    data_dir: Path | None = None,
    force: bool = False,
    test: bool = False,
) -> Path:
    """Download the ExtractBench dataset and reconstruct the sidecar layout.

    Uses huggingface_hub's snapshot_download (into the shared HF cache) to
    fetch the JSONL split files and source documents, then reconstructs the
    ``<split>/<stem>.pdf + <stem>.test.json`` layout under ``data_dir``.

    Args:
        data_dir: Local directory for the reconstructed dataset.
            Defaults to ./data (or ./data/test when ``test`` is set).
        force: Re-reconstruct (overwriting existing files) even if data
            already exists.
        test: Download the small test dataset (a few files per split)
            instead of the full dataset.

    Returns:
        Path to the reconstructed dataset directory.
    """
    from huggingface_hub import snapshot_download

    if data_dir is None:
        data_dir = default_data_dir(test=test)

    # Two branches, same as ParseBench: the full dataset lives on the default
    # branch, the small smoke subset on `test-data`. The resolved commit is
    # recorded in the manifest so `status` can report exactly what is on disk.
    revision = TEST_DATA_REVISION if test else None

    existing_manifest = read_manifest(data_dir)
    if existing_manifest is not None and existing_manifest.get("test") != test:
        kind_existing = "test subset" if existing_manifest.get("test") else "full dataset"
        kind_requested = "test subset" if test else "full dataset"
        raise RuntimeError(
            f"{data_dir} already holds the {kind_existing}; refusing to overlay the "
            f"{kind_requested} into the same directory. Use a different --data_dir."
        )

    if not force and is_dataset_ready(data_dir) and not _revision_is_stale(data_dir, revision):
        print(f"Dataset already downloaded at: {data_dir}")
        return data_dir

    label = "test dataset" if test else "dataset"
    print(f"Downloading {label} from HuggingFace: {DATASET_REPO}")
    if revision:
        print(f"Branch: {revision}")
    print(f"Destination: {data_dir}")

    snapshot_dir = Path(
        snapshot_download(
            repo_id=DATASET_REPO,
            repo_type=DATASET_REPO_TYPE,
            revision=revision,
        )
    )
    # huggingface_hub materializes snapshots under snapshots/<commit-sha>/.
    resolved_revision = snapshot_dir.name

    n_cases = 0
    per_split: dict[str, int] = {}
    written: set[Path] = set()
    for split in SPLITS:
        jsonl_path = snapshot_dir / f"{split}.jsonl"
        if not jsonl_path.exists():
            raise RuntimeError(f"Dataset snapshot is missing {split}.jsonl at {snapshot_dir}")
        split_dir = data_dir / split
        split_cases = 0
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            written.add(_write_sidecar(json.loads(line), split_dir, snapshot_dir, force=force))
            split_cases += 1
        per_split[split] = split_cases
        n_cases += split_cases

    orphans = _prune_orphans(data_dir, written)
    if orphans:
        print(f"Removed {len(orphans)} document(s) no longer in the dataset:")
        for path in orphans:
            print(f"  - {path.relative_to(data_dir)}")

    # Written last: its presence certifies a complete reconstruction.
    manifest = {
        "repo": DATASET_REPO,
        "revision": resolved_revision,
        "test": test,
        "cases": n_cases,
        "per_split": per_split,
    }
    (data_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    if not is_dataset_ready(data_dir):
        raise RuntimeError(f"Dataset download completed but validation failed. Check {data_dir} for missing files.")

    print(f"Dataset ready at: {data_dir} ({n_cases} test cases, revision {resolved_revision[:12]})")
    return data_dir
