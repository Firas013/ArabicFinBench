"""The schema validity gate: reject on invalid, do not merely report it.

Upstream computes ``schema_valid`` and aggregates
``confidence_full_gt_invalid_schema_fields``, but nothing acts on it — an
extraction that does not conform to its own declared schema is scored anyway,
and its score is reported beside conforming ones as though comparable.

This mirrors the admission gate in :mod:`arabicfinbench.gt.integrity`: a
document that fails validation is refused, by name, with every violation
listed. Refusing is the point. A extraction whose shape does not match the
schema it was asked for has not answered the question, and averaging it in
answers a different one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SchemaValidityError(ValueError):
    """An extraction does not conform to its declared schema."""

    def __init__(self, source: str, violations: list[str]) -> None:
        self.violations = violations
        listed = "; ".join(violations[:10])
        more = f" (+{len(violations) - 10} more)" if len(violations) > 10 else ""
        super().__init__(f"{source}: {len(violations)} schema violation(s): {listed}{more}")


@dataclass(frozen=True)
class SchemaValidation:
    """The outcome of validating one extraction against its schema."""

    valid: bool
    violations: tuple[str, ...] = field(default_factory=tuple)
    checked: bool = True  # False when no schema was declared to check against

    @property
    def summary(self) -> str:
        if not self.checked:
            return "no schema declared; nothing to validate against"
        return "valid" if self.valid else f"{len(self.violations)} violation(s)"


def validate_extraction(
    payload: Any,
    schema: dict[str, Any] | None,
    *,
    source: str = "extraction",
) -> SchemaValidation:
    """Validate an extraction against its JSON schema.

    Returns the outcome rather than raising, so a caller can report a whole
    run's validity before deciding what to refuse. Use :func:`gate` to refuse.

    A missing schema is reported as *not checked* rather than as valid: those
    are different states, and conflating them would let an undeclared schema
    look like a passed one.
    """
    if schema is None:
        return SchemaValidation(valid=True, checked=False)

    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover - dependency is declared
        return SchemaValidation(
            valid=True,
            checked=False,
            violations=("jsonschema is not installed; validation was skipped",),
        )

    validator = jsonschema.Draft7Validator(schema)
    violations = []
    for error in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.path) or "<root>"
        violations.append(f"{path}: {error.message}")
    return SchemaValidation(valid=not violations, violations=tuple(violations))


def gate(
    payload: Any,
    schema: dict[str, Any] | None,
    *,
    source: str = "extraction",
) -> SchemaValidation:
    """Validate and refuse on failure.

    :raises SchemaValidityError: listing every violation, with the source named.
    """
    outcome = validate_extraction(payload, schema, source=source)
    if outcome.checked and not outcome.valid:
        raise SchemaValidityError(source, list(outcome.violations))
    return outcome
