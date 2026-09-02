"""The scored-results store: score once, read many times.

Re-deriving every number on every read is slow, noisy, and — more importantly —
makes the reported table depend on whatever the code happened to be doing that
minute. A result is a measurement: it belongs on disk, stamped with the canon
version that produced it, and read back rather than recomputed.

The store is append-only JSONL, one line per (system, document, canon version).
Appending rather than overwriting means a re-score under a new canon version
sits beside the old one instead of silently replacing it, which is what makes
"did this number move, and why" answerable at all.

Reading returns the newest entry per (system, document) **at a given canon
version**, and refuses to mix versions in one table: two results scored under
different canon are not comparable, and the stamp exists to make that
checkable instead of remembered.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STORE = Path("results/scores.jsonl")


class MixedCanonError(ValueError):
    """A requested table would mix results scored under different canon versions."""


@dataclass(frozen=True)
class StoredScore:
    """One system's scored result for one document, as persisted."""

    system: str
    document: str
    canon_version: str
    scored_at: str
    passes: dict[str, dict[str, float]] = field(default_factory=dict)
    script_fidelity: float | None = None
    coverage: float | None = None
    numeric_exact: float | None = None
    digit_cer: float | None = None
    null_accuracy: float | None = None
    null_fabricated: float | None = None
    null_dropped: float | None = None
    null_judged: int = 0
    tables_paired: int = 0
    tables_actual: int = 0
    cost_per_page_usd: float | None = None
    median_latency_ms: float | None = None
    status: str = "api"  # api | hand-imported | externally-reported
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def raw_to_struct_delta(self) -> float | None:
        try:
            return self.passes["struct"]["table_record_match"] - self.passes["raw"]["table_record_match"]
        except KeyError:
            return None

    def to_json(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "document": self.document,
            "canon_version": self.canon_version,
            "scored_at": self.scored_at,
            "passes": self.passes,
            "script_fidelity": self.script_fidelity,
            "coverage": self.coverage,
            "numeric_exact": self.numeric_exact,
            "digit_cer": self.digit_cer,
            "null_accuracy": self.null_accuracy,
            "null_fabricated": self.null_fabricated,
            "null_dropped": self.null_dropped,
            "null_judged": self.null_judged,
            "tables_paired": self.tables_paired,
            "tables_actual": self.tables_actual,
            "cost_per_page_usd": self.cost_per_page_usd,
            "median_latency_ms": self.median_latency_ms,
            "status": self.status,
            "notes": list(self.notes),
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> StoredScore:
        payload = dict(payload)
        payload["notes"] = tuple(payload.get("notes") or ())
        return cls(**payload)


def from_document_score(
    score: Any,  # DocumentScore; typed loosely to keep this module import-light
    *,
    system: str,
    document: str,
    cost_per_page_usd: float | None = None,
    median_latency_ms: float | None = None,
    status: str = "api",
) -> StoredScore:
    """Flatten a DocumentScore into the persisted shape."""
    struct = score.passes.get("struct", {})
    return StoredScore(
        system=system,
        document=document,
        canon_version=score.canon_version,
        scored_at=datetime.now(UTC).isoformat(),
        passes=score.passes,
        script_fidelity=score.script_fidelity,
        coverage=score.coverage.coverage if score.coverage else None,
        numeric_exact=score.numeric.value_exact_match if score.numeric else None,
        digit_cer=score.numeric.digit_cer if score.numeric else None,
        null_accuracy=score.nulls.accuracy if score.nulls else None,
        null_fabricated=score.nulls.fabrication_rate if score.nulls else None,
        null_dropped=score.nulls.drop_rate if score.nulls else None,
        null_judged=score.nulls.considered if score.nulls else 0,
        tables_paired=int(struct.get("tables_paired", 0)),
        tables_actual=int(struct.get("tables_actual", 0)),
        cost_per_page_usd=cost_per_page_usd,
        median_latency_ms=median_latency_ms,
        status=status,
        notes=tuple(score.notes),
    )


def append(entries: list[StoredScore], *, store: Path = STORE) -> None:
    """Append entries. Never rewrites history: a re-score is a new line."""
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_json(), ensure_ascii=False) + "\n")


def load(*, store: Path = STORE) -> list[StoredScore]:
    """Every entry, in file order."""
    if not store.exists():
        return []
    return [
        StoredScore.from_json(json.loads(line))
        for line in store.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def latest(
    *,
    document: str | None = None,
    canon_version: str | None = None,
    store: Path = STORE,
) -> list[StoredScore]:
    """Newest entry per system, optionally filtered to one document/canon.

    :raises MixedCanonError: if the selection spans canon versions, naming them.
        Two results scored under different canon are not comparable, and
        silently showing them in one table is the error the stamp prevents.
    """
    entries = [e for e in load(store=store) if document is None or e.document == document]
    if canon_version is not None:
        entries = [e for e in entries if e.canon_version == canon_version]

    newest: dict[tuple[str, str], StoredScore] = {}
    for entry in entries:  # file order; later lines win
        newest[entry.system, entry.document] = entry
    selected = list(newest.values())

    versions = {e.canon_version for e in selected}
    if len(versions) > 1:
        raise MixedCanonError(
            f"selection spans canon versions {sorted(versions)}; re-score the older "
            f"systems or pass canon_version= to pick one"
        )
    return selected
