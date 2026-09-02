#!/usr/bin/env python3
"""Score systems into the results store, or render the leaderboard from it.

Two modes, deliberately separate:

``--record``
    Score the named pipelines once and append to ``results/scores.jsonl``.
    Run this when a system is new or the canon version changed.

``--show`` (default)
    Render the table from the store. No scoring, no GriTS, no API calls —
    reads numbers that were already measured and stamped.

Separating them is the point: a reported table should not depend on what the
code happened to be doing when someone asked to see it.

Usage::

    python scripts/afb_results.py --record --pipeline llamaparse_agentic ...
    python scripts/afb_results.py                      # show the table
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from arabicfinbench.canon.version import CANON_VERSION
from arabicfinbench.results import STORE, StoredScore, append, from_document_score, latest

DOCUMENT = "test_1/Test_1"


def _facts(pipeline: str, output_root: Path) -> tuple[float | None, float | None]:
    path = output_root / pipeline / "_evaluation_results.csv"
    if not path.exists():
        return None, None
    with path.open(encoding="utf-8") as f:
        row = next(csv.DictReader(f), None)
    if not row:
        return None, None
    cost = float(row["cost_per_page_usd"]) if row.get("cost_per_page_usd") else None
    latency = float(row["latency_ms"]) if row.get("latency_ms") else None
    return cost, latency


def record(pipelines: list[str], *, input_dir: Path, output_root: Path) -> list[StoredScore]:
    from arabicfinbench.scoring import score_document
    from extract_bench.test_cases.loader import load_test_cases

    cases = load_test_cases(input_dir, product_type="PARSE")
    entries: list[StoredScore] = []
    for pipeline in pipelines:
        for case in cases:
            result = output_root / pipeline / f"{case.test_id}.result.json"
            if not result.exists():
                # Guard 5: a failed call is scored zero and LISTED, never
                # skipped. A model missing from the table because its run died
                # is indistinguishable from one nobody tried.
                reason = _failure_reason(output_root / pipeline)
                entries.append(_failed_entry(pipeline, case.test_id, reason))
                print(f"  recorded {pipeline} as FAILED: {reason}")
                continue
            payload = json.loads(result.read_text(encoding="utf-8"))
            markdown = (payload.get("output") or {}).get("markdown") or ""
            score = score_document(case.expected_markdown or "", markdown, source=pipeline)
            cost, latency = _facts(pipeline, output_root)
            status = "hand-imported" if (payload.get("provenance") or {}).get("hand_imported") else "api"
            entries.append(
                from_document_score(
                    score,
                    system=pipeline,
                    document=case.test_id,
                    cost_per_page_usd=cost,
                    median_latency_ms=latency,
                    status=status,
                )
            )
            print(f"  recorded {pipeline} @ canon {score.canon_version}")
    return entries


def _failure_reason(output_dir: Path) -> str:
    """The provider's own error text, so a failure row says why."""
    errors = output_dir / "_errors.json"
    if not errors.exists():
        return "no inference result produced"
    try:
        payload = json.loads(errors.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "no inference result produced"
    items = payload if isinstance(payload, list) else payload.get("errors", [])
    for item in items:
        text = str((item or {}).get("error") or "").strip()
        if text:
            return text[:160]
    return "no inference result produced"


def _failed_entry(pipeline: str, document: str, reason: str) -> StoredScore:
    """A zeroed row that names its own cause."""
    from arabicfinbench.canon.version import CANON_VERSION
    from arabicfinbench.scoring import HEADLINE_METRICS, PASSES

    return StoredScore(
        system=pipeline,
        document=document,
        canon_version=CANON_VERSION,
        scored_at=datetime.now(UTC).isoformat(),
        passes={p: dict.fromkeys(HEADLINE_METRICS, 0.0) for p in PASSES},
        status="failed",
        notes=(reason,),
    )


def _fmt(value: float | None, places: int = 4) -> str:
    return "-" if value is None else f"{value:.{places}f}"


def _display_name(system: str) -> str:
    """The model's own name, for reading.

    Pipeline ids keep the ``or_`` prefix because the route is part of a row's
    identity — the same model served through OpenRouter and through its
    vendor's API can differ, and the store must not conflate them. The prefix
    is noise in a table a human reads, so it is dropped here and the routing is
    stated once in a footnote instead.
    """
    from arabicfinbench.pipelines import OPENROUTER_VLMS

    model = OPENROUTER_VLMS.get(system)
    if model:
        return model.split("/", 1)[-1]  # "qwen/qwen3.8-27b" -> "qwen3.8-27b"
    return system


def show(entries: list[StoredScore], *, hidden: list[StoredScore] | None = None) -> str:
    ranked = [e for e in entries if e.status != "failed"]
    ranked = sorted(ranked, key=lambda e: -(e.passes.get("struct", {}).get("table_record_match") or 0))
    canon = {e.canon_version for e in entries}
    out = [f"\n# ArabicFinBench — {DOCUMENT}  (canon {', '.join(sorted(canon))})\n"]
    out.append(
        "**What each column means: [docs/metrics.md](metrics.md).** In short — "
        "`struct` is the score, `raw` is what an unnormalised leaderboard would "
        "show, and the gap between them is convention rather than reading "
        "quality.\n"
    )

    out.append("## P — table metrics, raw | text | struct\n")
    out.append("| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |")
    out.append("|" + " --- |" * 8)
    for e in ranked:
        p = e.passes
        out.append(
            f"| {_display_name(e.system)} | {_fmt(p.get('raw', {}).get('table_record_match'))} | "
            f"{_fmt(p.get('text', {}).get('table_record_match'))} | "
            f"**{_fmt(p.get('struct', {}).get('table_record_match'))}** | "
            f"{_fmt(p.get('struct', {}).get('grits_con'))} | "
            f"{_fmt(e.raw_to_struct_delta)} | {e.tables_paired}/{e.tables_actual} | {e.status} |"
        )

    out.append("\n## P — cell metrics, and E — null correctness\n")
    out.append("| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |")
    out.append("|" + " --- |" * 8)
    for e in ranked:
        out.append(
            f"| {_display_name(e.system)} | {_fmt(e.coverage)} | {_fmt(e.numeric_exact)} | {_fmt(e.digit_cer)} | "
            f"{_fmt(e.null_accuracy)} | {_fmt(e.null_fabricated)} | {_fmt(e.null_dropped)} | {e.null_judged} |"
        )

    out.append("\n## Diagnostics\n")
    out.append("| system | script fidelity | $/page | latency | scored at |")
    out.append("|" + " --- |" * 5)
    for e in ranked:
        latency = "-" if e.median_latency_ms is None else f"{e.median_latency_ms / 1000:.1f}s"
        out.append(
            f"| {_display_name(e.system)} | {_fmt(e.script_fidelity)} | "
            f"{_fmt(e.cost_per_page_usd)} | {latency} | {e.scored_at[:19]} |"
        )

    out.append(
        "\n**F (arithmetic): not reported — no MATH rules are authored for this "
        "document yet. The mechanism exists and is tested; the rules are a "
        "ground-truth authoring task.**"
    )
    out.append("\n**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.")
    routed = sorted(_display_name(e.system) for e in ranked if e.system.startswith("or_"))
    if routed:
        # The or_ prefix carried this in the row name; with clean names the
        # routing has to be stated somewhere, because the same model served
        # through a different route can differ.
        out.append(
            "\n*Served via OpenRouter rather than the vendor's own API: "
            + ", ".join(routed)
            + ". The store keeps these under distinct ids so the two routes are never conflated.*"
        )
    failed = [e for e in entries if e.status == "failed"]
    if failed:
        out.append("\n## Did not produce output\n")
        out.append("| system | reason |")
        out.append("|" + " --- |" * 2)
        for e in failed:
            out.append(f"| {_display_name(e.system)} | {e.notes[0] if e.notes else 'unknown'} |")
        out.append(
            "\n*Scored zero on every dimension and listed here rather than "
            "dropped (guard 5). Ranked tables above exclude them: a zero from a "
            "failed call is not a measurement of reading quality.*"
        )

    if hidden:
        names = ", ".join(sorted(_display_name(e.system) for e in hidden))
        out.append(
            f"\n*Not shown: {names} — console exports whose tier, cost and latency cannot be "
            f"verified. Still recorded in `results/scores.jsonl`; `--include-hand-imported` "
            f"shows them.*"
        )
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", action="store_true", help="score and append to the store")
    ap.add_argument("--pipeline", action="append", default=[], help="pipeline to record (repeatable)")
    ap.add_argument("--input-dir", type=Path, default=Path("test_1"))
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    ap.add_argument("--out", type=Path, default=None, help="also write the rendered table here")
    ap.add_argument(
        "--include-hand-imported",
        action="store_true",
        help=(
            "also show console exports. Off by default: their tier, cost and "
            "latency are unverifiable, which is why the leaderboard refuses them"
        ),
    )
    args = ap.parse_args()

    if args.record:
        if not args.pipeline:
            print("--record needs at least one --pipeline")
            return 1
        entries = record(args.pipeline, input_dir=args.input_dir, output_root=args.output_root)
        append(entries)
        print(f"appended {len(entries)} entrie(s) to {STORE}")

    entries = latest(document=DOCUMENT, canon_version=CANON_VERSION)
    # Failures are not hidden — they get their own section. Only unverifiable
    # console exports are withheld, and only from the leaderboard view.
    hidden = [e for e in entries if e.status in ("hand-imported", "externally-reported")]
    if not args.include_hand_imported:
        entries = [e for e in entries if e.status not in ("hand-imported", "externally-reported")]
        table = show(entries, hidden=hidden)
    else:
        table = show(entries)
    print(table)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(table, encoding="utf-8")
        print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
