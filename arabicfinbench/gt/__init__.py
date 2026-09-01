"""Ground-truth integrity: validation, admission, and the audit trail.

The scoring side of the benchmark assumes the ground truth is right. That
assumption is earned here, not granted: every page passes schema validation
and an arithmetic admission gate before it can score anyone, models that
outvote the annotator trigger pixel re-verification, and corrections are
logged rather than silently applied. See gt/CONVENTIONS.md for the authoring
rules and :mod:`arabicfinbench.gt.integrity` for their enforcement.
"""

from arabicfinbench.gt.integrity import (
    AdmissionError,
    ConsensusFlag,
    GTSchemaError,
    Relation,
    admit_page,
    check_relations,
    consensus_flags,
    parse_amount,
    validate_gt_schema,
)

__all__ = [
    "AdmissionError",
    "ConsensusFlag",
    "GTSchemaError",
    "Relation",
    "admit_page",
    "check_relations",
    "consensus_flags",
    "parse_amount",
    "validate_gt_schema",
]
