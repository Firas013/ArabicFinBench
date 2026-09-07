"""Score the F axis: does the system's own output add up?

A relation is declared once and used twice. Against the ground truth it is the
admission gate -- a page whose printed totals do not reconcile is not scored,
because an unreconciled answer key penalises every system. Against a system's
extracted figures it is the F score: the same identity, asked of the reader
instead of the page.

That reuse is the point. Authoring a separate set of "F rules" would let the two
drift, and a benchmark whose answer key and whose arithmetic test disagree is
measuring neither.

**A relation the system did not fully extract fails as unevaluable rather than
passing vacuously.** A system that omits the components of a total would
otherwise score perfectly on arithmetic by declining to answer, which inverts
what the axis is for. The two outcomes are counted separately so "got the sum
wrong" and "never produced the figures" stay distinguishable.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from arabicfinbench.gt.integrity import AmountParseError, parse_amount


@dataclass(frozen=True)
class RelationOutcome:
    """One declared identity, evaluated against one system's figures."""

    name: str
    stated: Fraction | None
    computed: Fraction | None
    missing: tuple[str, ...]  # references the system did not produce

    @property
    def evaluable(self) -> bool:
        return not self.missing and self.stated is not None and self.computed is not None

    @property
    def reconciles(self) -> bool:
        return self.evaluable and self.stated == self.computed

    @property
    def residual(self) -> Fraction | None:
        if self.stated is None or self.computed is None:
            return None
        return self.stated - self.computed


@dataclass(frozen=True)
class ArithmeticReport:
    """The F axis for one system on one document."""

    outcomes: tuple[RelationOutcome, ...]

    @property
    def declared(self) -> int:
        return len(self.outcomes)

    @property
    def evaluable(self) -> int:
        return sum(1 for o in self.outcomes if o.evaluable)

    @property
    def reconciling(self) -> int:
        return sum(1 for o in self.outcomes if o.reconciles)

    @property
    def unevaluable(self) -> int:
        return self.declared - self.evaluable

    @property
    def consistency(self) -> float | None:
        """Share of declared relations the system's own figures satisfy.

        Denominator is every declared relation, not the evaluable ones: a
        relation the system could not supply figures for is a relation it
        failed to demonstrate, and moving it out of the denominator would pay a
        system for silence. ``None`` only when nothing was declared -- an
        absence of rules is not a score of zero.
        """
        if not self.outcomes:
            return None
        return self.reconciling / self.declared

    @property
    def evaluable_consistency(self) -> float | None:
        """Share of the relations it *could* evaluate that it got right.

        Reported beside :attr:`consistency` because the two separate a system
        that computes badly from one that extracts sparsely.
        """
        if not self.evaluable:
            return None
        return self.reconciling / self.evaluable


def _amount(raw: str | None) -> Fraction | None:
    if raw is None:
        return None
    try:
        return parse_amount(raw)
    except AmountParseError:
        return None


def score_relations(
    relations: list[dict],
    values: dict[str, str | None],
) -> ArithmeticReport:
    """Evaluate declared relations against one system's extracted figures.

    :param relations: ``{"name", "total", "addends"}`` with reference strings.
    :param values: reference -> the system's value, or None where it produced
        nothing at that position.
    """
    outcomes: list[RelationOutcome] = []
    for relation in relations:
        name = str(relation.get("name") or "<unnamed>")
        total_ref = str(relation["total"])
        addend_refs = [str(a) for a in relation["addends"]]

        stated = _amount(values.get(total_ref))
        missing = [total_ref] if stated is None else []

        computed: Fraction | None = Fraction(0)
        for ref in addend_refs:
            raw = values.get(ref)
            # An empty cell is a legitimate nil in these statements; a cell the
            # system never produced is not the same claim and is recorded.
            if raw is None:
                missing.append(ref)
                continue
            if not str(raw).strip() or str(raw).strip() == "-":
                continue
            amount = _amount(raw)
            if amount is None:
                missing.append(ref)
                continue
            computed += amount

        if missing:
            computed = None
        outcomes.append(RelationOutcome(name=name, stated=stated, computed=computed, missing=tuple(missing)))
    return ArithmeticReport(outcomes=tuple(outcomes))
