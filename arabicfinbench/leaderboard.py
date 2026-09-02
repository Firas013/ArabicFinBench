"""The leaderboard generator, and everything it refuses to do.

Refusals are the point. A leaderboard is where unfairness becomes permanent —
a wrong number in a terminal is a bug, a wrong number in a published table is a
citation — so the generator enforces at emission time what the rest of the
benchmark enforces at scoring time:

- **No row without provenance** (guard 4): adapter, model version, named mode,
  canon version, cost, latency, seeds, timestamp, page-image hashes, prompt
  hash. A missing field rejects the row with :class:`MissingProvenanceError`
  naming it.
- **No hand-imported rows** (guard 4): they appear in the dev report, labelled;
  the leaderboard requires the API adapter path.
- **No unknown adapters** (guard 9): the adapter must be registered in this
  public repository — anyone must be able to read the code that produced a row.
- **Seed policy honoured** (guard 6): a nondeterministic adapter's row must
  carry 3 seeds; a deterministic adapter's single-seed row says so in print.
- **Never one number** (guard 10): there is no code path that emits a combined
  P/E/F or "overall" score. Asking for one raises
  :class:`CombinedScoreError`; CI greps emitted tables for an overall column
  besides.
- **Raw next to canon, always** (guard 3): every table carries
  raw | text | struct plus the raw→struct delta and script fidelity.
- The reference implementation is labelled as such on every row it appears in
  (guard 7).
"""

from __future__ import annotations

from dataclasses import dataclass

from arabicfinbench.determinism import DeterminismPolicy, check_seed_count
from arabicfinbench.provenance import Provenance
from arabicfinbench.scoring import PASSES, DocumentScore

REFERENCE_LABEL = "reference implementation, benchmark authors"

# The word that must never appear as a column. CI greps for it too.
_FORBIDDEN_COLUMN = "overall"


class CombinedScoreError(ValueError):
    """Someone asked for one number. The benchmark does not have one.

    P, E, and F fail in qualitatively different ways; averaging them ranks a
    system that fabricates well-formed wrong figures above one that never
    miscalculates. There is no code path around this error on purpose.
    """


class UnknownAdapterError(ValueError):
    """The row's adapter is not registered in this repository.

    Inclusion criterion: adapter code lives in the public repo, so every row
    is reproducible from source by a reader.
    """


@dataclass(frozen=True)
class LeaderboardRow:
    """One adapter's scored documents plus the provenance that admits them."""

    provenance: Provenance
    scores: dict[str, DocumentScore]  # test_id -> score
    determinism: DeterminismPolicy | None = None


def known_adapters() -> set[str]:
    """Adapter names registered in this public repository."""
    from extract_bench.inference.pipelines import list_pipelines  # type: ignore[import-untyped]

    return set(list_pipelines())


def validate_row(row: LeaderboardRow) -> None:
    """Every admission check, in order of least-forgivable failure first.

    :raises HandImportedResultError: hand imports belong in the dev report.
    :raises MissingProvenanceError: naming every absent field.
    :raises UnknownAdapterError: adapter code must live in this repository.
    :raises SeedPolicyError: seed count must satisfy the determinism class.
    """
    row.provenance.validate_for_leaderboard()
    if row.provenance.adapter not in known_adapters():
        raise UnknownAdapterError(
            f"adapter '{row.provenance.adapter}' is not registered in this repository; "
            f"leaderboard rows require public adapter code"
        )
    if row.determinism is not None and row.provenance.seed_count is not None:
        check_seed_count(row.determinism, row.provenance.seed_count)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pass_means(row: LeaderboardRow, metric: str) -> dict[str, float | None]:
    """Per-pass mean for one metric, None where the metric is absent."""
    out: dict[str, float | None] = {}
    for pass_name in PASSES:
        values = [s.passes[pass_name][metric] for s in row.scores.values() if metric in s.passes.get(pass_name, {})]
        out[pass_name] = _mean(values) if values else None
    return out


def _fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.4f}"


def _row_label(provenance: Provenance) -> str:
    label = f"{provenance.adapter} ({provenance.model_version}, {provenance.mode})"
    if provenance.reference_implementation:
        label += f" — {REFERENCE_LABEL}"
    return label


def build_leaderboard(
    rows: list[LeaderboardRow],
    *,
    metrics: tuple[str, ...],
    combined: bool = False,
) -> str:
    """Emit the leaderboard as a markdown table: per metric, every pass.

    :param combined: There is no acceptable value of True.
    :raises CombinedScoreError: if a combined score is requested.
    """
    if combined:
        raise CombinedScoreError(
            "refusing to emit a combined score: P, E, and F are reported per "
            "dimension, raw and canon, never as one number"
        )
    for row in rows:
        validate_row(row)

    lines: list[str] = []
    for metric in metrics:
        if metric.lower() == _FORBIDDEN_COLUMN:
            raise CombinedScoreError(f"refusing to emit a column named '{metric}'")
        lines.append(f"\n### {metric}\n")
        header = "| system | " + " | ".join(PASSES) + " | raw→struct Δ | script fidelity | seeds |"
        lines.append(header)
        lines.append("|" + " --- |" * (len(PASSES) + 4))
        for row in rows:
            per_pass = _pass_means(row, metric)
            raw_v, struct_v = per_pass["raw"], per_pass["struct"]
            delta_s = "-" if raw_v is None or struct_v is None else f"{struct_v - raw_v:+.4f}"
            fidelities = [s.script_fidelity for s in row.scores.values() if s.script_fidelity is not None]
            fidelity = f"{_mean(fidelities):.4f}" if fidelities else "-"
            seeds = str(row.provenance.seed_count)
            if row.determinism is not None:
                seeds += f" ({row.determinism.report_note})"
            cells = " | ".join(_fmt(per_pass[p]) for p in PASSES)
            lines.append(f"| {_row_label(row.provenance)} | {cells} | {delta_s} | {fidelity} | {seeds} |")
    return "\n".join(lines) + "\n"


def build_dev_report(rows: list[LeaderboardRow], *, metrics: tuple[str, ...]) -> str:
    """The permissive sibling: hand imports allowed, loudly labelled.

    Provenance gaps do not reject a row here — the dev report is where gaps
    get noticed — but each row states what it is, and nothing from this
    function is a leaderboard.
    """
    lines = ["\n## Dev report (not a leaderboard)\n"]
    for metric in metrics:
        lines.append(f"\n### {metric}\n")
        lines.append("| system | " + " | ".join(PASSES) + " | script fidelity | status |")
        lines.append("|" + " --- |" * (len(PASSES) + 3))
        for row in rows:
            per_pass = _pass_means(row, metric)
            fidelities = [s.script_fidelity for s in row.scores.values() if s.script_fidelity is not None]
            fidelity = f"{_mean(fidelities):.4f}" if fidelities else "-"
            if row.provenance.external_report:
                who = row.provenance.reported_by or "unattributed"
                status = f"EXTERNALLY REPORTED ({who}); not re-derived"
            elif row.provenance.hand_imported:
                status = "hand-imported (dev only)"
            else:
                status = "api"
            missing = row.provenance.missing_fields()
            if missing and not (row.provenance.hand_imported or row.provenance.external_report):
                status += f"; missing provenance: {', '.join(missing)}"
            cells = " | ".join(_fmt(per_pass[p]) for p in PASSES)
            lines.append(f"| {_row_label(row.provenance)} | {cells} | {fidelity} | {status} |")
    return "\n".join(lines) + "\n"
