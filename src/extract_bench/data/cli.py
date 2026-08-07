"""Command-line interface for data management."""

import sys
from pathlib import Path

from extract_bench.data.download import default_data_dir, download_dataset, is_dataset_ready, read_manifest


class DataCLI:
    """Command-line interface for managing the benchmark dataset."""

    def download(
        self,
        data_dir: str | Path | None = None,
        force: bool = False,
        test: bool = False,
    ) -> int:
        """Download the ExtractBench dataset from HuggingFace.

        Reconstructs the sidecar layout (<split>/<stem>.pdf + <stem>.test.json)
        that inference and evaluation consume.

        Args:
            data_dir: Local directory to store the dataset
                (default: ./data, or ./data/test when --test is set)
            force: Force re-download even if data already exists
            test: Download the small test dataset (6 documents: 3 short, 2 medium, 1 long)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            data_path = Path(data_dir) if data_dir else default_data_dir(test=test)
            download_dataset(data_dir=data_path, force=force, test=test)
            return 0
        except Exception as e:
            print(f"Error downloading dataset: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return 1

    def status(
        self,
        data_dir: str | Path | None = None,
        test: bool = False,
    ) -> int:
        """Check if the dataset is downloaded and show per-split counts.

        Args:
            data_dir: Data directory to check
                (default: ./data, or ./data/test when --test is set)
            test: Check the small test dataset instead of the full dataset

        Returns:
            Exit code (0 if ready, 1 if not)
        """
        data_path = Path(data_dir) if data_dir else default_data_dir(test=test)
        if not is_dataset_ready(data_path):
            print(f"Dataset is NOT ready at: {data_path}")
            print("Run 'extract-bench download' to download it.")
            return 1

        print(f"Dataset: {data_path}")
        manifest = read_manifest(data_path)
        if manifest and manifest.get("revision"):
            print(f"Revision: {manifest['revision'][:12]}")
        print()
        total = 0
        hdr = f"{'Split':<12} {'Test Cases':>12}"
        print(hdr)
        print("-" * len(hdr))
        for split_dir in sorted(p for p in data_path.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
            if split_dir.name == "test":
                continue  # nested test subset, reported via --test
            n = sum(1 for _ in split_dir.rglob("*.test.json"))
            if n == 0:
                continue
            total += n
            print(f"{split_dir.name:<12} {n:>12,}")
        print("-" * len(hdr))
        print(f"{'Total':<12} {total:>12,}")
        return 0
