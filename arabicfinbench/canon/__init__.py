"""Canonical forms used to normalise Arabic financial values, labels, and tables.

Applied to both the ground truth and a system's output before comparison — by
:mod:`arabicfinbench.scoring`, which enforces the symmetry structurally — so a
score reflects what a system read rather than which transcription conventions it
happened to share with the annotator.

Two kinds, for two kinds of disagreement:

- :mod:`arabicfinbench.canon.text` — how a value is *written*: numerals,
  separators, negatives, diacritics, invisible marks, spacing.
- :mod:`arabicfinbench.canon.structure` — how a table is *shaped*: section
  headers, blank spacer rows, column direction.

Every transform is a named rule; traced application reports which rules fired.
`CANON_VERSION` is stamped into every scored result.
"""

from arabicfinbench.canon.structure import (
    Section,
    TableReport,
    canonical_column_order,
    canonicalize_structure,
    canonicalize_table_structure,
    fold_header_markup,
    is_blank_row,
    is_section_row,
    normalize_table_columns,
    strip_sections,
    strip_table_sections,
)
from arabicfinbench.canon.text import (
    canonicalize,
    canonicalize_markup,
    canonicalize_markup_traced,
    canonicalize_traced,
    fold_letter_variants,
    fold_numerals,
    fold_paren_negatives,
    normalize_era_marker_spacing,
    normalize_spacing,
    strip_diacritics,
    strip_invisibles,
)
from arabicfinbench.canon.version import CANON_VERSION

__all__ = [
    "CANON_VERSION",
    "Section",
    "TableReport",
    "canonical_column_order",
    "canonicalize",
    "canonicalize_markup",
    "canonicalize_markup_traced",
    "canonicalize_structure",
    "canonicalize_table_structure",
    "fold_header_markup",
    "canonicalize_traced",
    "fold_letter_variants",
    "fold_numerals",
    "fold_paren_negatives",
    "is_blank_row",
    "is_section_row",
    "normalize_era_marker_spacing",
    "normalize_spacing",
    "normalize_table_columns",
    "strip_diacritics",
    "strip_invisibles",
    "strip_sections",
    "strip_table_sections",
]
