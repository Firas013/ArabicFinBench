"""Enforcement for the ground-truth rules in gt/CONVENTIONS.md.

Three mechanisms, each guarding a way a benchmark quietly starts scoring its
own annotation noise instead of the models:

Schema validation
    A malformed page fails loudly at authoring time, naming the defect — not
    at scoring time as a mysterious zero.

Arithmetic admission gate
    A financial statement is self-checking: totals are sums of their
    components. A page is admitted only when every *declared* relation
    reconciles exactly; a page with no declared relations is not admitted at
    all, because an unchecked page is an unearned assumption. Cells no
    relation can reach are tagged ``arithmetic_blind`` and reported as their
    own line — the errors arithmetic cannot catch deserve their own
    visibility, not silence.

Consensus-against-GT
    When two or more independent systems agree on a value that differs from
    the ground truth, the likeliest error is the annotator's. The cell is
    flagged for pixel re-verification and the outcome logged in
    ``gt/corrections.log.jsonl`` — corrections are an audit trail, never a
    silent edit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from arabicfinbench.canon import canonicalize

# Thousands-grouped integers and decimal-comma numbers are both legitimate in
# these statements; each is parsed by its own unambiguous shape, and anything
# else is refused rather than guessed at.
_GROUPED_RE = re.compile(r"^-?\d{1,3}(,\d{3})+$")
_PLAIN_RE = re.compile(r"^-?\d+$")
_DECIMAL_COMMA_RE = re.compile(r"^-?\d+,\d{1,2}$|^-?\d+,\d{4,}$")
_DECIMAL_POINT_RE = re.compile(r"^-?\d+\.\d+$")


class GTSchemaError(ValueError):
    """A ground-truth page violates the schema or an authoring convention."""


class AdmissionError(ValueError):
    """A ground-truth page failed the arithmetic admission gate."""


class AmountParseError(ValueError):
    """A cell that a relation references cannot be read as an amount."""


@dataclass(frozen=True)
class Relation:
    """One declared arithmetic identity: total == sum(addends).

    Cells are addressed as ``[row, col]`` into ``tables[table].rows``.
    """

    name: str
    table: int
    total: tuple[int, int]
    addends: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class RelationResult:
    relation: Relation
    stated: Fraction
    computed: Fraction

    @property
    def reconciles(self) -> bool:
        return self.stated == self.computed


@dataclass(frozen=True)
class ReconciliationReport:
    results: tuple[RelationResult, ...]
    arithmetic_blind: tuple[str, ...] = field(default_factory=tuple)

    @property
    def failures(self) -> tuple[RelationResult, ...]:
        return tuple(r for r in self.results if not r.reconciles)


@dataclass(frozen=True)
class ConsensusFlag:
    """A cell where independent systems outvote the ground truth."""

    table: int
    row: int
    col: int
    gt_value: str
    consensus_value: str
    agreeing_systems: tuple[str, ...]


def validate_gt_schema(payload: Any, *, source: str = "gt") -> None:
    """Refuse a malformed or convention-violating ground-truth page.

    :raises GTSchemaError: naming every defect found, not just the first.
    """
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise GTSchemaError(f"{source}: top level must be an object, got {type(payload).__name__}")

    lines = payload.get("lines")
    if not isinstance(lines, list):
        errors.append("'lines' must be a list")
    else:
        for i, line in enumerate(lines):
            if not isinstance(line, dict) or not isinstance(line.get("text"), str):
                errors.append(f"lines[{i}] must be an object with a string 'text'")

    tables = payload.get("tables")
    if not isinstance(tables, list):
        errors.append("'tables' must be a list")
    else:
        for t, table in enumerate(tables):
            rows = table.get("rows") if isinstance(table, dict) else None
            if not isinstance(rows, list) or not rows:
                errors.append(f"tables[{t}] must have a non-empty 'rows' list")
                continue
            widths = set()
            for r, row in enumerate(rows):
                if not isinstance(row, list) or not all(isinstance(c, str) for c in row):
                    errors.append(f"tables[{t}].rows[{r}] must be a list of strings")
                    continue
                widths.add(len(row))
                if row and not any(canonicalize(c) for c in row):
                    # CONVENTIONS.md §3: blank spacer rows are parser artefacts;
                    # ground truth must not encode them.
                    errors.append(f"tables[{t}].rows[{r}] is blank (conventions §3: do not encode spacer rows)")
            if len(widths) > 1:
                errors.append(f"tables[{t}] is ragged: row widths {sorted(widths)} (one grid per table)")

    if errors:
        raise GTSchemaError(f"{source}: " + "; ".join(errors))


def parse_amount(cell: str, *, source: str = "cell") -> Fraction:
    """Read one financial amount, exactly, from either numeral script.

    Canon folds the script and the accounting-negative parentheses; this
    resolves the two comma meanings by shape — ``24,061,612`` groups
    thousands, ``0,0258`` is a decimal — and refuses anything ambiguous
    instead of guessing. ``-`` is nil by convention.

    :raises AmountParseError: for a cell no rule covers, by name.
    """
    canonical = canonicalize(cell)
    if canonical in ("-", ""):
        return Fraction(0)
    if _GROUPED_RE.match(canonical):
        return Fraction(canonical.replace(",", ""))
    if _PLAIN_RE.match(canonical):
        return Fraction(canonical)
    if _DECIMAL_COMMA_RE.match(canonical):
        return Fraction(canonical.replace(",", "."))
    if _DECIMAL_POINT_RE.match(canonical):
        return Fraction(canonical)
    raise AmountParseError(f"{source}: cannot read {cell!r} (canonical {canonical!r}) as an amount")


def _cell(payload: dict[str, Any], table: int, addr: tuple[int, int], *, name: str) -> str:
    try:
        return str(payload["tables"][table]["rows"][addr[0]][addr[1]])
    except (IndexError, KeyError, TypeError) as exc:
        raise AdmissionError(f"relation '{name}' addresses a missing cell: table {table}, cell {list(addr)}") from exc


def check_relations(
    payload: dict[str, Any],
    relations: list[Relation],
    *,
    arithmetic_blind: list[str] | None = None,
) -> ReconciliationReport:
    """Evaluate every declared relation against the page, exactly."""
    results = []
    for rel in relations:
        stated = parse_amount(
            _cell(payload, rel.table, rel.total, name=rel.name),
            source=f"{rel.name}: total",
        )
        computed = sum(
            (
                parse_amount(_cell(payload, rel.table, addr, name=rel.name), source=f"{rel.name}: addend {list(addr)}")
                for addr in rel.addends
            ),
            start=Fraction(0),
        )
        results.append(RelationResult(relation=rel, stated=stated, computed=computed))
    return ReconciliationReport(results=tuple(results), arithmetic_blind=tuple(arithmetic_blind or ()))


def admit_page(
    payload: dict[str, Any],
    relations: list[Relation],
    *,
    arithmetic_blind: list[str] | None = None,
    source: str = "gt",
) -> ReconciliationReport:
    """The gate: schema-valid, relations declared, every relation reconciling.

    :raises GTSchemaError: for schema or convention violations.
    :raises AdmissionError: when no relations are declared (an unchecked page
        is an unearned assumption) or any declared relation fails, with the
        stated and computed values named.
    """
    validate_gt_schema(payload, source=source)
    if not relations:
        raise AdmissionError(
            f"{source}: no arithmetic relations declared; a page whose totals are "
            f"never checked cannot be admitted (declare relations, or the page is out)"
        )
    report = check_relations(payload, relations, arithmetic_blind=arithmetic_blind)
    if report.failures:
        details = "; ".join(f"{r.relation.name}: stated {r.stated} != computed {r.computed}" for r in report.failures)
        raise AdmissionError(f"{source}: {len(report.failures)} relation(s) do not reconcile: {details}")
    return report


def consensus_flags(
    gt_tables: list[list[list[str]]],
    system_tables: dict[str, list[list[list[str]]]],
    *,
    min_agreeing: int = 2,
) -> list[ConsensusFlag]:
    """Cells where at least ``min_agreeing`` systems agree against the GT.

    Grids are compared positionally, cell text under canon. Positions any
    system cannot address (shorter table, different segmentation) are skipped
    for that system rather than guessed — consensus requires actual agreement,
    not coincidence of absence.
    """
    flags: list[ConsensusFlag] = []
    for t, gt_table in enumerate(gt_tables):
        for r, gt_row in enumerate(gt_table):
            for c, gt_cell in enumerate(gt_row):
                gt_value = canonicalize(gt_cell)
                votes: dict[str, list[str]] = {}
                for system, tables in system_tables.items():
                    try:
                        value = canonicalize(tables[t][r][c])
                    except IndexError:
                        continue
                    if value and value != gt_value:
                        votes.setdefault(value, []).append(system)
                for value, systems in votes.items():
                    if len(systems) >= min_agreeing:
                        flags.append(
                            ConsensusFlag(
                                table=t,
                                row=r,
                                col=c,
                                gt_value=gt_value,
                                consensus_value=value,
                                agreeing_systems=tuple(sorted(systems)),
                            )
                        )
    return flags
