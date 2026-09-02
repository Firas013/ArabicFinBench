#!/usr/bin/env python3
"""Run the OpenRouter VLM pipelines and record their provenance.

The pipelines live in :mod:`arabicfinbench.pipelines` rather than upstream's
registry, so they must be registered before the harness can resolve them. This
script does that, then hands off to the harness's own inference CLI — the same
code path ``extract-bench run`` uses, so a VLM row is produced exactly as any
other row is.

It also writes the tracked provenance declaration for each model, including the
frozen prompt hash. That hash is the difference between "we ran four models"
and "we ran four models on equal terms".

Usage::

    python scripts/afb_run_openrouter.py --input-dir test_1
    python scripts/afb_run_openrouter.py --input-dir test_1 --only or_gpt_5_mini
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arabicfinbench.pipelines import (
    OPENROUTER_VLMS,
    PROMPT_SHA256,
    register_arabicfinbench_pipelines,
)

RUNS_DIR = Path("arabicfinbench/runs")


def _declare(pipeline: str, model: str) -> None:
    """Write the tracked operator declaration for one VLM row."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"{pipeline}.json").write_text(
        json.dumps(
            {
                "model_version": f"openrouter:{model}",
                "mode": "vlm-transcription",
                "seed_count": 1,
                "sampled": False,
                "prompt_sha256": PROMPT_SHA256,
                "_prompt_note": (
                    "Frozen transcription prompt shared byte-identically by every VLM "
                    "row (arabicfinbench/pipelines.py::PARSE_PROMPT). Editing it changes "
                    "this hash, which is the intended alarm: results produced under "
                    "different prompts are not comparable."
                ),
                "_route_note": (
                    "Served via OpenRouter, not the vendor's own API. The same model "
                    "on a different route can differ; the or_ prefix keeps the two "
                    "from being conflated."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", type=Path, default=Path("test_1"))
    ap.add_argument("--only", action="append", default=[], help="run just these pipelines")
    ap.add_argument("--max-concurrent", type=int, default=4)
    ap.add_argument(
        "--force",
        action="store_true",
        help="re-run even when a stored result exists (needed after a config change)",
    )
    args = ap.parse_args()

    # The harness CLI loads .env in its own entry point; calling InferenceCLI
    # directly bypasses that, and the provider then sends no Authorization
    # header at all — which OpenRouter reports as a confusing "no cookie auth".
    from dotenv import load_dotenv

    load_dotenv(".env", override=False)

    import os

    from extract_bench.inference.cli import InferenceCLI  # type: ignore[import-untyped]
    from extract_bench.inference.pipelines import register_pipeline  # type: ignore[import-untyped]

    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set (checked environment and .env)")
        return 1

    register_arabicfinbench_pipelines(register_pipeline)
    targets = args.only or list(OPENROUTER_VLMS)
    print(f"prompt sha256: {PROMPT_SHA256}\n")

    cli = InferenceCLI()
    failures: list[str] = []
    for pipeline in targets:
        model = OPENROUTER_VLMS.get(pipeline)
        if model is None:
            print(f"  unknown pipeline {pipeline!r}; known: {sorted(OPENROUTER_VLMS)}")
            failures.append(pipeline)
            continue
        print(f"=== {pipeline}  ({model}) ===")
        try:
            code = cli.run(
                pipeline=pipeline,
                input_dir=args.input_dir,
                max_concurrent=args.max_concurrent,
                force=args.force,
                force_exit_on_completion=False,
            )
        except Exception as exc:  # noqa: BLE001 - one model failing must not stop the sweep
            print(f"  {pipeline} raised: {type(exc).__name__}: {exc}")
            failures.append(pipeline)
            continue
        if code != 0:
            failures.append(pipeline)
        _declare(pipeline, model)

    if failures:
        # Named, not swallowed: a model missing from the table must be missing
        # for a reason someone can read.
        print(f"\nfailed: {failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
