"""Canonical forms used to normalise Arabic financial values, labels, and tables.

Applied to both the ground truth and a system's output before comparison, so a
score reflects what a system read rather than which transcription conventions it
happened to share with the annotator.

Two kinds, for two kinds of disagreement:

- :mod:`arabicfinbench.canon.text` — how a value is *written*: numerals,
  separators, diacritics, invisible marks, spacing.
- :mod:`arabicfinbench.canon.structure` — how a table is *shaped*: section
  headers encoded as a sparse row or as a full-width span.
"""

from arabicfinbench.canon.structure import (
    Section,
    TableReport,
    is_blank_row,
    is_section_row,
    strip_sections,
    strip_table_sections,
)
from arabicfinbench.canon.text import (
    canonicalize,
    canonicalize_markup,
    fold_letter_variants,
    fold_numerals,
    normalize_era_marker_spacing,
    normalize_spacing,
    strip_diacritics,
    strip_invisibles,
)

__all__ = [
    "Section",
    "TableReport",
    "canonicalize",
    "canonicalize_markup",
    "fold_letter_variants",
    "fold_numerals",
    "is_blank_row",
    "is_section_row",
    "normalize_era_marker_spacing",
    "normalize_spacing",
    "strip_diacritics",
    "strip_invisibles",
    "strip_sections",
    "strip_table_sections",
]
