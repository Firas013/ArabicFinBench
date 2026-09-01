"""Canonical forms used to normalise Arabic financial values and labels.

Applied to both the ground truth and a system's output before comparison, so a
score reflects what a system read rather than which transcription conventions
it happened to share with the annotator. See :mod:`arabicfinbench.canon.text`.
"""

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
    "canonicalize",
    "canonicalize_markup",
    "fold_letter_variants",
    "fold_numerals",
    "normalize_era_marker_spacing",
    "normalize_spacing",
    "strip_diacritics",
    "strip_invisibles",
]
