"""The F axis: arithmetic consistency of the figures a system extracted.

A financial statement is self-checking. Totals are sums of their components,
closing balances are opening balances rolled forward, a note reconciles to the
line it supports. A system can read every glyph correctly and still produce a
statement that does not add up — and one that does add up is making a claim no
per-cell metric tests.

This fills ``ParseRuleType.MATH``, which existed in the taxonomy with no schema,
no evaluator, and no dispatcher entry. Filling the socket keeps arithmetic a
*rule type* inside the existing engine rather than a parallel dimension with its
own runner and its own reporting path.

Semantics come from :func:`arabicfinbench.gt.integrity.check_relations`: exact
``Fraction`` reconciliation, no float tolerance. Where the page itself is
imprecise — a printed rate rounded to four decimals, multiplied by a base — the
imprecision is declared as a ``tolerance_band`` rather than smuggled in as a
global epsilon, so the reason a comparison is loose is written down next to the
rule that needs it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from arabicfinbench.canon import canonicalize
from arabicfinbench.gt.integrity import AmountParseError, parse_amount


class MathRuleType(StrEnum):
    """What kind of identity a math rule asserts."""

    BLOCK_SUM = "block_sum"  # a total equals the sum of its components
    ROLL_FORWARD = "roll_forward"  # opening + movements == closing
    CROSS_STATEMENT = "cross_statement"  # same figure in two statements agrees
    NOTE_TO_LINE = "note_to_line"  # a note's total equals the line it supports
    TOLERANCE_BAND = "tolerance_band"  # rate x base, where the printed rate is rounded


@dataclass(frozen=True)
class MathResult:
    """One evaluated identity."""

    rule_id: str
    math_type: MathRuleType
    stated: Fraction | None
    computed: Fraction | None
    low: Fraction | None
    high: Fraction | None
    passed: bool
    reason: str

    @property
    def residual(self) -> Fraction | None:
        if self.stated is None or self.computed is None:
            return None
        return self.stated - self.computed


def _band_from_printed_rate(rate_text: str, base: Fraction) -> tuple[Fraction, Fraction]:
    """The interval a rounded printed rate admits when applied to a base.

    A rate printed as ``٠,٠٢٥٨`` is any true rate in
    ``[0.02575, 0.02585)`` — half a unit of the last printed decimal either
    way. Multiplying that interval by the base gives the range of products the
    page could legitimately show. Scoring against the midpoint instead would
    fail a correct statement for the publisher's rounding.
    """
    rate = parse_amount(rate_text)
    # Precision comes from what the page actually printed, not from the parsed
    # value: 0.0258 and 0.02580 are the same number but the second claims a
    # tighter rate and so admits a narrower band.
    printed = canonicalize(rate_text)
    fraction_digits = printed.split(",")[-1] if "," in printed else printed.split(".")[-1] if "." in printed else ""
    decimals = len(fraction_digits) if fraction_digits.isdigit() and ("," in printed or "." in printed) else 0
    half_ulp = Fraction(1, 10**decimals) / 2
    return (rate - half_ulp) * base, (rate + half_ulp) * base


def _tolerance_for(addend_count: int, per_addend: Fraction) -> Fraction:
    """Rounding tolerance scaled by how many rounded figures were added.

    Each addend printed to the nearest unit can be off by half a unit, and
    those errors accumulate; a fixed tolerance would be too tight for a long
    block and too loose for a short one.
    """
    return per_addend * addend_count


def evaluate_math_rule(
    rule: dict,
    values: dict[str, str],
) -> MathResult:
    """Evaluate one math rule against a system's extracted values.

    :param rule: The rule payload (see ``ParseMathRule``).
    :param values: Cell reference -> the system's value for it. A reference the
        system did not produce is absent; the rule then fails as *unevaluable*
        rather than passing vacuously, because a missing figure is exactly the
        case a system could otherwise exploit.
    """
    rule_id = str(rule.get("id") or "<unnamed>")
    math_type = MathRuleType(rule.get("math_type", MathRuleType.BLOCK_SUM))

    def amount(ref: str) -> Fraction | None:
        raw = values.get(ref)
        if raw is None:
            return None
        try:
            return parse_amount(raw, source=f"{rule_id}:{ref}")
        except AmountParseError:
            return None

    total_ref = str(rule.get("total", ""))
    addend_refs = [str(a) for a in (rule.get("addends") or [])]

    stated = amount(total_ref)
    if stated is None:
        return MathResult(
            rule_id,
            math_type,
            None,
            None,
            None,
            None,
            False,
            f"total {total_ref!r} was not extracted or is not a readable amount",
        )

    if math_type is MathRuleType.TOLERANCE_BAND:
        base_ref = str(rule.get("base", ""))
        base = amount(base_ref)
        rate_text = rule.get("rate")
        if base is None or rate_text is None:
            return MathResult(
                rule_id,
                math_type,
                stated,
                None,
                None,
                None,
                False,
                f"tolerance_band needs a readable base {base_ref!r} and a printed rate",
            )
        low, high = _band_from_printed_rate(str(rate_text), base)
        passed = low <= stated <= high
        return MathResult(
            rule_id,
            math_type,
            stated,
            None,
            low,
            high,
            passed,
            (
                f"{stated} within [{low}, {high}] admitted by printed rate {rate_text}"
                if passed
                else f"{stated} outside [{low}, {high}] admitted by printed rate {rate_text}"
            ),
        )

    parts: list[Fraction] = []
    for ref in addend_refs:
        part = amount(ref)
        if part is None:
            return MathResult(
                rule_id,
                math_type,
                stated,
                None,
                None,
                None,
                False,
                f"addend {ref!r} was not extracted or is not a readable amount",
            )
        parts.append(part)

    computed = sum(parts, start=Fraction(0))
    per_addend = Fraction(str(rule.get("tolerance", 0)))
    tolerance = _tolerance_for(len(parts), per_addend)
    passed = abs(stated - computed) <= tolerance
    return MathResult(
        rule_id,
        math_type,
        stated,
        computed,
        None,
        None,
        passed,
        (
            f"{stated} == {computed}" + (f" within tolerance {tolerance}" if tolerance else "")
            if passed
            else f"{stated} != {computed} (residual {stated - computed}, tolerance {tolerance})"
        ),
    )


def evaluate_math_rules(rules: list[dict], values: dict[str, str]) -> list[MathResult]:
    """Evaluate every math rule, in order."""
    return [evaluate_math_rule(rule, values) for rule in rules]


def arithmetic_pass_rate(results: list[MathResult]) -> float:
    """Fraction of declared identities that reconcile.

    Zero when no rules were declared: a statement nobody checked has not
    demonstrated that it adds up, and reporting 1.0 would say it had.
    """
    return sum(1 for r in results if r.passed) / len(results) if results else 0.0
