"""Tests for the F axis: arithmetic consistency via ParseRuleType.MATH.

The unfairness this prevents: a system can read every glyph correctly and
still produce a statement that does not add up, and no per-cell metric tests
that. It also prevents the opposite error — failing a correct statement for
the publisher's own rounding, which is what a global epsilon would do.

``MATH`` was a dead enum value: declared in the taxonomy with no schema, no
evaluator and no dispatcher entry.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from arabicfinbench.dimensions.arithmetic.rule import (
    MathRuleType,
    arithmetic_pass_rate,
    evaluate_math_rule,
    evaluate_math_rules,
)


class TestTheEnumIsNoLongerDead:
    def test_a_math_rule_now_coerces_to_a_typed_model(self) -> None:
        from extract_bench.test_cases.parse_rule_schemas import ParseMathRule, coerce_parse_rule

        rule = coerce_parse_rule(
            {"type": "math", "id": "r1", "math_type": "block_sum", "total": "t", "addends": ["a", "b"]}
        )
        assert isinstance(rule, ParseMathRule)
        assert rule.math_type == "block_sum"

    def test_the_rule_carries_its_declared_metadata(self) -> None:
        from extract_bench.test_cases.parse_rule_schemas import coerce_parse_rule

        rule = coerce_parse_rule(
            {
                "type": "math",
                "id": "r2",
                "math_type": "roll_forward",
                "total": "closing",
                "addends": ["opening", "movement"],
                "period": "2024",
                "scope": "statement_of_changes_in_equity",
                "unit": "SAR",
                "applicability": "annual only",
                "tolerance": "0.5",
            }
        )
        assert rule.period == "2024"
        assert rule.scope == "statement_of_changes_in_equity"
        assert rule.unit == "SAR"
        assert rule.applicability == "annual only"

    def test_an_unknown_math_type_is_rejected(self) -> None:
        from extract_bench.test_cases.parse_rule_schemas import coerce_parse_rule

        with pytest.raises(Exception):  # noqa: B017 - pydantic validation error type is internal
            coerce_parse_rule({"type": "math", "math_type": "invented", "total": "t"})


class TestBlockSum:
    RULE = {"id": "current_assets", "math_type": "block_sum", "total": "T", "addends": ["a", "b"]}

    def test_a_reconciling_block_passes(self) -> None:
        values = {"T": "٢٤,٩٠١,٤٣٣", "a": "٨٣٩,٨٢١", "b": "٢٤,٠٦١,٦١٢"}
        result = evaluate_math_rule(self.RULE, values)
        assert result.passed
        assert result.residual == 0

    def test_script_does_not_affect_reconciliation(self) -> None:
        values = {"T": "24,901,433", "a": "٨٣٩,٨٢١", "b": "24,061,612"}
        assert evaluate_math_rule(self.RULE, values).passed

    def test_a_wrong_total_fails_and_names_the_residual(self) -> None:
        values = {"T": "٢٤,٩٠١,٤٣٤", "a": "٨٣٩,٨٢١", "b": "٢٤,٠٦١,٦١٢"}
        result = evaluate_math_rule(self.RULE, values)
        assert not result.passed
        assert result.residual == 1
        assert "residual 1" in result.reason

    def test_a_missing_addend_fails_rather_than_passing_vacuously(self) -> None:
        # The case a system could otherwise exploit: drop a figure, and an
        # identity that can no longer be checked scores as satisfied.
        result = evaluate_math_rule(self.RULE, {"T": "٢٤,٩٠١,٤٣٣", "a": "٨٣٩,٨٢١"})
        assert not result.passed
        assert "'b'" in result.reason

    def test_a_missing_total_fails(self) -> None:
        result = evaluate_math_rule(self.RULE, {"a": "١", "b": "٢"})
        assert not result.passed
        assert "'T'" in result.reason

    def test_an_unreadable_amount_fails_rather_than_being_skipped(self) -> None:
        result = evaluate_math_rule(self.RULE, {"T": "غير مقروء", "a": "١", "b": "٢"})
        assert not result.passed


class TestToleranceScalesWithAddends:
    def test_a_long_block_gets_proportionally_more_room(self) -> None:
        # Four figures each rounded to the nearest unit can be off by 2 in
        # total; a fixed tolerance would be too tight here.
        rule = {
            "id": "long",
            "math_type": "block_sum",
            "total": "T",
            "addends": ["a", "b", "c", "d"],
            "tolerance": "0.5",
        }
        values = {"T": "102", "a": "25", "b": "25", "c": "25", "d": "25"}
        assert evaluate_math_rule(rule, values).passed  # residual 2, tolerance 4 * 0.5

    def test_the_same_residual_fails_a_short_block(self) -> None:
        rule = {"id": "short", "math_type": "block_sum", "total": "T", "addends": ["a"], "tolerance": "0.5"}
        assert not evaluate_math_rule(rule, {"T": "102", "a": "100"}).passed  # residual 2 > 0.5

    def test_zero_tolerance_is_exact(self) -> None:
        rule = {"id": "exact", "math_type": "block_sum", "total": "T", "addends": ["a"]}
        assert not evaluate_math_rule(rule, {"T": "100.01", "a": "100"}).passed


class TestToleranceBand:
    """The worked example: a printed rate is rounded, so the product is a range."""

    RULE = {
        "id": "zakat",
        "math_type": "tolerance_band",
        "total": "zakat",
        "base": "pool",
        "rate": "٠,٠٢٥٨",
    }

    def test_the_printed_zakat_passes(self) -> None:
        # rate 0.0258 on base 19,245,096 admits [495,561, 497,486];
        # the statement prints 497,437.
        result = evaluate_math_rule(self.RULE, {"zakat": "٤٩٧,٤٣٧", "pool": "١٩,٢٤٥,٠٩٦"})
        assert result.passed, result.reason

    def test_the_band_matches_the_worked_bounds(self) -> None:
        result = evaluate_math_rule(self.RULE, {"zakat": "٤٩٧,٤٣٧", "pool": "١٩,٢٤٥,٠٩٦"})
        assert result.low is not None and result.high is not None
        assert int(result.low) == 495_561
        assert int(result.high) == 497_485  # 497,485.73 -> the printed 497,486 rounds from this

    def test_the_exact_midpoint_product_would_also_pass(self) -> None:
        midpoint = Fraction(258, 10000) * 19_245_096
        result = evaluate_math_rule(self.RULE, {"zakat": str(int(midpoint)), "pool": "١٩,٢٤٥,٠٩٦"})
        assert result.passed

    def test_a_figure_outside_the_band_fails(self) -> None:
        result = evaluate_math_rule(self.RULE, {"zakat": "٥٠٠,٠٠٠", "pool": "١٩,٢٤٥,٠٩٦"})
        assert not result.passed
        assert "outside" in result.reason

    def test_a_more_precisely_printed_rate_admits_a_narrower_band(self) -> None:
        # 0.02580 claims more precision than 0.0258 and must be held to it.
        loose = evaluate_math_rule(self.RULE, {"zakat": "٤٩٧,٤٣٧", "pool": "١٩,٢٤٥,٠٩٦"})
        tight_rule = {**self.RULE, "rate": "٠,٠٢٥٨٠"}
        tight = evaluate_math_rule(tight_rule, {"zakat": "٤٩٧,٤٣٧", "pool": "١٩,٢٤٥,٠٩٦"})
        assert tight.high is not None and loose.high is not None
        assert tight.high < loose.high

    def test_a_missing_base_fails_rather_than_passing(self) -> None:
        result = evaluate_math_rule(self.RULE, {"zakat": "٤٩٧,٤٣٧"})
        assert not result.passed


class TestRollForwardAndOtherTypes:
    def test_roll_forward_reconciles_opening_plus_movements(self) -> None:
        rule = {
            "id": "equity",
            "math_type": "roll_forward",
            "total": "closing",
            "addends": ["opening", "income"],
        }
        values = {"opening": "١١,٣٦٩,٤١٩", "income": "١,٠٩٥,٦٤٨", "closing": "١٢,٤٦٥,٠٦٧"}
        assert evaluate_math_rule(rule, values).passed

    def test_cross_statement_agreement(self) -> None:
        rule = {"id": "x", "math_type": "cross_statement", "total": "balance_sheet", "addends": ["equity_stmt"]}
        assert evaluate_math_rule(rule, {"balance_sheet": "١٨,٩١٥,٠٦٧", "equity_stmt": "١٨,٩١٥,٠٦٧"}).passed

    def test_note_to_line_agreement(self) -> None:
        rule = {"id": "n", "math_type": "note_to_line", "total": "line", "addends": ["note_total"]}
        assert evaluate_math_rule(rule, {"line": "٤,٢٨٠,٨١١", "note_total": "٤,٢٨٠,٨١١"}).passed

    def test_the_type_is_carried_onto_the_result(self) -> None:
        rule = {"id": "n", "math_type": "note_to_line", "total": "a", "addends": ["b"]}
        result = evaluate_math_rule(rule, {"a": "١", "b": "١"})
        assert result.math_type is MathRuleType.NOTE_TO_LINE


class TestPassRate:
    def test_all_reconciling_is_one(self) -> None:
        rules = [
            {"id": "a", "total": "T", "addends": ["x"]},
            {"id": "b", "total": "T", "addends": ["x"]},
        ]
        results = evaluate_math_rules(rules, {"T": "٥", "x": "٥"})
        assert arithmetic_pass_rate(results) == pytest.approx(1.0)

    def test_no_declared_rules_is_zero_not_one(self) -> None:
        # A statement nobody checked has not shown that it adds up.
        assert arithmetic_pass_rate([]) == 0.0

    def test_a_mixed_set_reports_the_fraction(self) -> None:
        rules = [
            {"id": "ok", "total": "T", "addends": ["x"]},
            {"id": "bad", "total": "T", "addends": ["y"]},
        ]
        results = evaluate_math_rules(rules, {"T": "٥", "x": "٥", "y": "٦"})
        assert arithmetic_pass_rate(results) == pytest.approx(0.5)
