"""The F axis: arithmetic consistency, and the relations that define it.

Two properties matter more than the score itself.

**The declared relations must admit the ground truth.** They are the answer
key's own self-check: a page whose printed totals do not reconcile penalises
every system for the annotator's arithmetic. This test is the reason the six
test_6 corrections were found at all.

**A system cannot earn arithmetic credit by declining to answer.** If a relation
whose figures were never extracted counted as passing — or were dropped from the
denominator — the highest F score would go to a system that outputs nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arabicfinbench.dimensions.arithmetic.score import score_relations
from arabicfinbench.gt.integrity import Relation, check_relations
from arabicfinbench.gt.relations import BY_DOCUMENT, for_document

DATASET = Path("dataset")

RELATIONS = [
    {"name": "total", "total": "t0.r2.c0", "addends": ["t0.r0.c0", "t0.r1.c0"]},
]


class TestUnevaluableCannotPass:
    def test_a_relation_with_no_figures_does_not_reconcile(self) -> None:
        report = score_relations(RELATIONS, {})
        assert report.declared == 1
        assert report.reconciling == 0
        assert report.evaluable == 0
        assert report.consistency == 0.0
        # Nothing was evaluable, so the restricted rate has nothing to report.
        assert report.evaluable_consistency is None

    def test_a_missing_addend_is_not_treated_as_zero(self) -> None:
        # 100 = 100 + <missing>. Treating the absent cell as zero would pass.
        report = score_relations(RELATIONS, {"t0.r2.c0": "100", "t0.r0.c0": "100", "t0.r1.c0": None})
        assert report.reconciling == 0
        assert report.outcomes[0].missing == ("t0.r1.c0",)

    def test_a_printed_empty_cell_is_a_nil_not_a_gap(self) -> None:
        # An empty cell is a legitimate value in these statements; only a cell
        # the system never produced counts as missing.
        report = score_relations(RELATIONS, {"t0.r2.c0": "100", "t0.r0.c0": "100", "t0.r1.c0": ""})
        assert report.reconciling == 1
        assert report.consistency == 1.0

    def test_correct_arithmetic_reconciles(self) -> None:
        report = score_relations(RELATIONS, {"t0.r2.c0": "٣٠٠", "t0.r0.c0": "١٠٠", "t0.r1.c0": "٢٠٠"})
        assert report.reconciling == 1

    def test_one_wrong_digit_fails(self) -> None:
        report = score_relations(RELATIONS, {"t0.r2.c0": "301", "t0.r0.c0": "100", "t0.r1.c0": "200"})
        assert report.reconciling == 0
        assert report.evaluable == 1  # it answered; it was wrong
        assert report.outcomes[0].residual == 1


def _relation_objects(rules: list[dict]) -> list[Relation]:
    """Convert authored references into ground-truth Relation objects."""

    def ref(text: str) -> tuple[int, int, int]:
        t, r, c = text.split(".")
        return int(t[1:]), int(r[1:]), int(c[1:])

    out = []
    for rule in rules:
        table, row, col = ref(rule["total"])
        out.append(
            Relation(
                name=rule["name"],
                table=table,
                total=(row, col),
                addends=tuple((ref(a)[1], ref(a)[2]) for a in rule["addends"]),
            )
        )
    return out


@pytest.mark.parametrize("document", sorted(BY_DOCUMENT))
def test_declared_relations_reconcile_against_the_ground_truth(document: str) -> None:
    """The answer key must satisfy its own arithmetic.

    ``test_6`` carries one known exception, logged as an open flag in
    ``gt/corrections.log.jsonl`` rather than deleted: removing an inconvenient
    relation is how a benchmark stops noticing its own defects.
    """
    directory, stem = document.split("/")
    path = DATASET / directory / f"{stem}.json"
    if not path.exists():
        pytest.skip(f"{path} not present (corpus documents are not committed)")

    payload = json.loads(path.read_text(encoding="utf-8"))
    rules = for_document(document)
    assert rules, f"{document} declares no relations"

    report = check_relations(payload, _relation_objects(rules))
    known_open = {"total_assets_c1"} if document == "test_6/Test_6" else set()
    unexpected = [r.relation.name for r in report.failures if r.relation.name not in known_open]
    assert not unexpected, f"{document}: {unexpected} do not reconcile"
