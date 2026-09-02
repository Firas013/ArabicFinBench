#!/usr/bin/env python3
"""Assemble leaderboard rows from stored runs — and let the generator refuse.

Provenance is derived mechanically wherever the harness already recorded it
(mode from the pipeline config, cost and latency from the evaluation CSV,
timestamps from the result file, page-image hashes from the source PDF) and
supplemented from ``output/<pipeline>/_afb_provenance.json`` for what only the
operator knows (model version string, seed count). Nothing is invented: a gap
survives into the row and the generator rejects the row by the gap's name.

Hand-imported results are detected from their stamped provenance and shown in
the dev report only; the leaderboard requires the API adapter path.

Usage::

    python scripts/afb_leaderboard.py --pipeline llamaparse_agentic \\
        --pipeline datalab_accurate --pipeline datalab_web --input-dir test_1
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from arabicfinbench.canon.version import CANON_VERSION
from arabicfinbench.determinism import declare
from arabicfinbench.leaderboard import LeaderboardRow, build_dev_report, build_leaderboard, validate_row
from arabicfinbench.provenance import NO_PROMPT, Provenance, page_image_hashes
from arabicfinbench.scoring import DocumentScore, score_document
from extract_bench.test_cases.loader import load_test_cases

METRICS = ("table_record_match", "grits_trm_composite", "grits_con")


def _harness_facts(output_dir: Path) -> dict:
    """Provenance the harness already recorded, taken from its artefacts."""
    facts: dict = {}
    metadata_path = output_dir / "_metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        config = (metadata.get("pipeline") or {}).get("config") or {}
        facts["mode"] = str(config.get("mode") or config.get("tier") or "")
    csv_path = output_dir / "_evaluation_results.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if rows:
            costs = [float(r["cost_per_page_usd"]) for r in rows if r.get("cost_per_page_usd")]
            latencies = sorted(float(r["latency_ms"]) for r in rows if r.get("latency_ms"))
            if costs:
                facts["cost_per_page_usd"] = sum(costs) / len(costs)
            if latencies:
                facts["median_latency_ms"] = latencies[len(latencies) // 2]
    return facts


RUNS_DIR = Path("arabicfinbench/runs")
EXTERNAL_DIR = RUNS_DIR / "external"


def _external_rows(cases: list) -> list[LeaderboardRow]:
    """Rows whose scores were reported from elsewhere, not re-derived here.

    Recorded so a system run on another machine can sit beside the others for
    discussion, and labelled so nobody mistakes it for a measured row. The
    leaderboard rejects them; only the dev report shows them.
    """
    from arabicfinbench.scoring import reported_score

    rows: list[LeaderboardRow] = []
    for path in sorted(EXTERNAL_DIR.glob("*.json")) if EXTERNAL_DIR.is_dir() else []:
        payload = json.loads(path.read_text(encoding="utf-8"))
        document = payload.get("document") or (cases[0].test_id if cases else "unknown")
        score = reported_score(
            payload.get("reported_scores") or {},
            script_fidelity=payload.get("reported_script_fidelity"),
            source=payload.get("reported_by", path.name),
            canon_version=payload.get("reported_canon_version", "unknown"),
        )
        rows.append(
            LeaderboardRow(
                provenance=Provenance(
                    adapter=payload.get("display_name") or payload.get("adapter") or path.stem,
                    model_version=str(payload.get("model_version", "")),
                    mode=str(payload.get("mode", "")),
                    canon_version=str(payload.get("reported_canon_version", "")),
                    cost_per_page_usd=payload.get("cost_per_page_usd"),
                    median_latency_ms=payload.get("median_latency_ms"),
                    seed_count=payload.get("seed_count"),
                    run_timestamp=str(payload.get("run_timestamp", "")),
                    page_image_hashes=tuple(payload.get("page_image_hashes", ())),
                    prompt_sha256=str(payload.get("prompt_sha256", "")),
                    reference_implementation=bool(payload.get("reference_implementation", False)),
                    external_report=True,
                    reported_by=str(payload.get("reported_by", "")),
                ),
                scores={document: score},
            )
        )
    return rows


def _operator_declaration(pipeline: str, output_dir: Path) -> dict:
    """Operator-stated provenance: tracked declaration, then local override.

    The tracked file in ``arabicfinbench/runs/`` is the auditable one — a
    statement that gates leaderboard admission cannot live only in untracked
    scratch that ``rm -rf output/`` destroys. The copy beside the run output
    still wins when present, for local iteration before a declaration is
    committed.
    """
    declaration: dict = {}
    tracked = RUNS_DIR / f"{pipeline}.json"
    if tracked.exists():
        declaration.update(json.loads(tracked.read_text(encoding="utf-8")))
    local = output_dir / "_afb_provenance.json"
    if local.exists():
        declaration.update(json.loads(local.read_text(encoding="utf-8")))
    # Keys documented as commentary, never provenance fields.
    return {k: v for k, v in declaration.items() if not k.startswith("_")}


def _build_row(
    pipeline: str,
    output_root: Path,
    cases: list,
    pdf_hashes: dict[str, tuple[str, ...]],
) -> LeaderboardRow:
    output_dir = output_root / pipeline
    scores: dict[str, DocumentScore] = {}
    hand_imported = False
    run_timestamp = ""
    all_hashes: list[str] = []

    for case in cases:
        result_path = output_dir / f"{case.test_id}.result.json"
        if not result_path.exists():
            continue
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        if (payload.get("provenance") or {}).get("hand_imported"):
            hand_imported = True
        run_timestamp = run_timestamp or str(payload.get("started_at") or "")
        markdown = (payload.get("output") or {}).get("markdown") or ""
        scores[case.test_id] = score_document(
            case.expected_markdown or "", markdown, source=f"{pipeline}/{case.test_id}"
        )
        all_hashes.extend(pdf_hashes.get(case.test_id, ()))

    facts = _harness_facts(output_dir)
    overrides = _operator_declaration(pipeline, output_dir)

    provenance = Provenance(
        adapter=pipeline,
        model_version=str(overrides.get("model_version", "")),
        mode=str(overrides.get("mode", facts.get("mode", ""))),
        canon_version=CANON_VERSION,
        cost_per_page_usd=overrides.get("cost_per_page_usd", facts.get("cost_per_page_usd")),
        median_latency_ms=overrides.get("median_latency_ms", facts.get("median_latency_ms")),
        seed_count=overrides.get("seed_count"),
        run_timestamp=str(overrides.get("run_timestamp", run_timestamp)),
        page_image_hashes=tuple(all_hashes),
        prompt_sha256=str(overrides.get("prompt_sha256", NO_PROMPT)),
        hand_imported=hand_imported,
        reference_implementation=bool(overrides.get("reference_implementation", False)),
    )
    determinism = declare(pipeline, sampled=bool(overrides.get("sampled", False)))
    return LeaderboardRow(provenance=provenance, scores=scores, determinism=determinism)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pipeline", required=True, action="append")
    ap.add_argument("--input-dir", required=True, type=Path)
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    ap.add_argument("--out", type=Path, default=None, help="write the leaderboard markdown here (stdout otherwise)")
    args = ap.parse_args()

    cases = load_test_cases(args.input_dir, product_type="PARSE")
    pdf_hashes = {case.test_id: page_image_hashes(Path(case.file_path)) for case in cases}

    rows = [_build_row(p, args.output_root, cases, pdf_hashes) for p in args.pipeline]
    rows += _external_rows(cases)

    admitted: list[LeaderboardRow] = []
    print("== admission ==")
    for row in rows:
        try:
            validate_row(row)
        except Exception as exc:  # noqa: BLE001 - every rejection is reported, by type and name
            print(f"  REJECTED {row.provenance.adapter}: {type(exc).__name__}: {exc}")
        else:
            print(f"  admitted {row.provenance.adapter}")
            admitted.append(row)

    print(build_dev_report(rows, metrics=METRICS))

    if admitted:
        table = build_leaderboard(admitted, metrics=METRICS)
        if args.out:
            args.out.write_text(table, encoding="utf-8")
            print(f"leaderboard written to {args.out}")
        else:
            print("== leaderboard (admitted rows only) ==")
            print(table)
    else:
        print("no rows admitted to the leaderboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
