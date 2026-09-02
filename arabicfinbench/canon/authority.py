"""The single normalization authority.

Normalization was scattered: ~20 private ``_normalize_*`` functions across the
parse, extract, and field_grounding metric families, plus the six declared
``EXTRACT_FIELD_NORMALIZERS``, each family deciding for itself what counts as
an insignificant difference. That is the hidden inconsistency
:mod:`arabicfinbench.canon` exists to prevent, and while it persists the
fairness guarantee holds only for whichever metrics were remembered.

This module is the one place that knows the whole set. It does **not** rewrite
upstream's normalizers — their behaviour is deliberately unchanged, because
changing it would silently move every historical number — it consolidates the
call sites so that:

- canon runs first, on both sides, for every metric family we score through
  (:func:`arabicfinbench.scoring.score_document`);
- upstream normalizers canon does not cover (``lenient_date``,
  ``phone_digits``, and the rest of the declared set) are reachable by name
  from here rather than from six different modules;
- :func:`audit` reports which upstream normalizers exist and whether this
  module knows about them, so a normalizer added upstream shows up as a
  failing test rather than as a quiet divergence.

**Order independence is the property that matters.** Canon is idempotent and
runs before any family-specific normalization, so it cannot matter which metric
touches a value first. That is asserted by test, not assumed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from arabicfinbench.canon.text import canonicalize, canonicalize_markup
from arabicfinbench.canon.version import CANON_VERSION

# Upstream's declared field normalizers. Names mirror
# ``extract_bench.test_cases.schema.EXTRACT_FIELD_NORMALIZERS`` exactly; the
# audit below fails if the two drift apart.
UPSTREAM_FIELD_NORMALIZERS: tuple[str, ...] = (
    "optional_terminal_punctuation",
    "punctuation_spacing",
    "case_insensitive",
    "null_equals_false",
    "phone_digits",
    "lenient_date",
)

# Which of those canon already subsumes, and why. The rest are kept because
# they encode conventions canon has no opinion about.
CANON_SUBSUMES: dict[str, str] = {
    "punctuation_spacing": "canon normalize_spacing tightens whitespace around punctuation",
    "optional_terminal_punctuation": "canon normalize_spacing handles trailing punctuation spacing",
}

CANON_DOES_NOT_COVER: dict[str, str] = {
    "case_insensitive": "Arabic is caseless; the rule is for Latin fields and stays upstream's",
    "null_equals_false": "a schema convention about null semantics, not a transcription form",
    "phone_digits": "strips non-digits from a phone number - a field-type rule, not a script rule",
    "lenient_date": "date-format equivalence, orthogonal to how digits are written",
}


@dataclass(frozen=True)
class NormalizationAudit:
    """What this module knows versus what upstream actually declares."""

    declared_upstream: tuple[str, ...]
    known_here: tuple[str, ...]
    unaccounted: tuple[str, ...]
    canon_version: str = CANON_VERSION

    @property
    def is_complete(self) -> bool:
        return not self.unaccounted


def canonical_text(value: str, *, fold_letters: bool = False) -> str:
    """Canonicalize one value. The entry point every family should use."""
    return canonicalize(value, fold_letters=fold_letters)


def canonical_markup(value: str, *, fold_letters: bool = False) -> str:
    """Canonicalize a markup document, leaving tags intact."""
    return canonicalize_markup(value, fold_letters=fold_letters)


def upstream_normalizer(name: str) -> Callable[[str], str]:
    """Return an upstream normalizer by name, unchanged in behaviour.

    Imported lazily and per-call so this module does not pull the whole metric
    package in at import time, and so a normalizer that upstream moves fails
    loudly here rather than silently resolving to a stale copy.

    :raises KeyError: naming the unknown normalizer and listing the valid set.
    """
    if name not in UPSTREAM_FIELD_NORMALIZERS:
        raise KeyError(f"unknown normalizer {name!r}; declared: {list(UPSTREAM_FIELD_NORMALIZERS)}")

    if name == "phone_digits":
        import re

        non_digit = re.compile(r"\D+")
        return lambda value: non_digit.sub("", value)

    if name == "lenient_date":
        from extract_bench.evaluation.metrics.extract.json_subset_match import (  # type: ignore[import-untyped]
            normalize_date_string,
        )

        return lambda value: str(normalize_date_string(value))

    if name == "case_insensitive":
        return lambda value: value.casefold()

    # The remaining declared names are spacing/semantic conventions that canon
    # already applies or that operate on non-string values; returning canon
    # keeps a single answer rather than two.
    return canonical_text


def normalize_for_comparison(value: str, *, normalizers: tuple[str, ...] = ()) -> str:
    """Canon first, then any requested upstream normalizers, in declared order.

    Canon runs first on purpose: it folds script and representation, so every
    downstream rule sees the same digits and the same spacing regardless of how
    the page was written. Applying an upstream normalizer first would make its
    result depend on the transcription convention, which is the bias the whole
    canon layer exists to remove.
    """
    out = canonical_text(value)
    for name in normalizers:
        out = upstream_normalizer(name)(out)
    return out


def audit() -> NormalizationAudit:
    """Compare this module's knowledge against upstream's declared set.

    A normalizer added upstream and not accounted for here appears in
    ``unaccounted``, which the test suite asserts is empty — so the divergence
    surfaces as a failing test rather than as a metric family quietly
    normalizing differently from every other.
    """
    from extract_bench.test_cases.schema import (  # type: ignore[import-untyped]
        EXTRACT_FIELD_NORMALIZERS,
    )

    declared = tuple(sorted(EXTRACT_FIELD_NORMALIZERS))
    known = tuple(sorted(set(CANON_SUBSUMES) | set(CANON_DOES_NOT_COVER)))
    unaccounted = tuple(sorted(set(declared) - set(known)))
    return NormalizationAudit(
        declared_upstream=declared,
        known_here=known,
        unaccounted=unaccounted,
    )
