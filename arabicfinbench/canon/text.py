"""Canonical forms for comparing Arabic financial text.

Two systems can transcribe the same balance-sheet cell in ways that differ in
every byte and in no fact: ``٨٣٩,٨٢١`` and ``839,821`` are the same number, and
``٢٠٢٣ م`` and ``٢٠٢٣م`` are the same year. Scoring those as mismatches measures
typography, not document understanding, and it does so in a direction that
flatters whichever system happens to share the ground truth's conventions.

Canonicalisation is therefore applied to *both* sides before any comparison —
never to the ground truth alone, which would merely move the bias rather than
remove it.

The transforms are split into two tiers:

``canonicalize(..., fold_letters=False)``
    Representational only. Digits, separators, diacritics, invisible
    directional marks, and spacing around punctuation. These change how a value
    is written, never which value it is, so they are safe to apply by default.

``canonicalize(..., fold_letters=True)``
    Additionally folds orthographic variants (alef and ya forms, ta marbuta).
    Standard practice for Arabic retrieval, but genuinely lossy: it can merge
    two distinct spellings. Opt-in, and reported separately so a score can never
    silently depend on it.
"""

from __future__ import annotations

import re
import unicodedata

# Arabic-Indic (U+0660–0669) and Extended/Persian Arabic-Indic (U+06F0–06F9).
_DIGIT_MAP = {
    **{0x0660 + i: str(i) for i in range(10)},
    **{0x06F0 + i: str(i) for i in range(10)},
}

# Arabic-script separators carry the same meaning as their ASCII counterparts.
_SEPARATOR_MAP = {
    0x066B: ".",  # ARABIC DECIMAL SEPARATOR
    0x066C: ",",  # ARABIC THOUSANDS SEPARATOR
    0x066A: "%",  # ARABIC PERCENT SIGN
}

_NUMERIC_MAP = {**_DIGIT_MAP, **_SEPARATOR_MAP}

# Harakat and other combining marks. U+0670 (superscript alef) is included; the
# range stops short of U+0660 so digits are never caught here.
_DIACRITICS = re.compile(r"[ً-ٰٟۖ-ۜ۟-۪ۨ-ۭ]")

# Tatweel is a justification glyph with no phonetic or semantic content.
_TATWEEL = re.compile(r"ـ+")

# Bidi controls and zero-width characters are invisible, so a mismatch caused by
# one is always an artefact.
_INVISIBLE = re.compile(r"[​-‏‪-‮⁦-⁩﻿]")

# Punctuation that should not carry a leading space, in both scripts.
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,،.؛;:!؟?%\)\]])")
_SPACE_AFTER_OPEN = re.compile(r"([\(\[])\s+")

# Era markers: ``م`` (ميلادي, Gregorian) and ``ه`` (هجري, Hijri) trail a year with
# optional space — ``٢٠٢٤ م`` and ``٢٠٢٤م`` are the same year. The tatweel in the
# common ``هـ`` spelling is already gone by the time this runs. The trailing
# ``(?!\w)`` keeps the rule from biting into a longer word that merely starts
# with one of these letters.
_ERA_MARKER = re.compile(r"(\d)\s+([مه])(?!\w)")

_LETTER_FOLD_MAP = {
    # Alef forms → bare alef.
    0x0623: "ا",  # أ
    0x0625: "ا",  # إ
    0x0622: "ا",  # آ
    0x0671: "ا",  # ٱ
    # Alef maqsura → ya.
    0x0649: "ي",  # ى
    # Ta marbuta → ha.
    0x0629: "ه",  # ة
}

# Splits a markup string into tags and the text between them, so canonicalising
# a document never rewrites an attribute value such as colspan="4".
_TAG_SPLIT = re.compile(r"(<[^>]*>)")


def fold_numerals(text: str) -> str:
    """Map Arabic-Indic digits and Arabic separators to their ASCII forms."""
    return text.translate(_NUMERIC_MAP)


def strip_diacritics(text: str) -> str:
    """Remove harakat, other combining marks, and tatweel."""
    return _TATWEEL.sub("", _DIACRITICS.sub("", text))


def strip_invisibles(text: str) -> str:
    """Remove bidi control characters and zero-width space variants."""
    return _INVISIBLE.sub("", text)


def fold_letter_variants(text: str) -> str:
    """Fold orthographic variants of alef, alef maqsura, and ta marbuta.

    Lossy: distinct spellings can collapse onto one form. Callers opt in.
    """
    return text.translate(_LETTER_FOLD_MAP)


def normalize_era_marker_spacing(text: str) -> str:
    """Close the optional space between a year and its era marker.

    ``٢٠٢٤ م`` and ``٢٠٢٤م`` denote the same year; the space is a typesetting
    choice that annotators and parsers make independently.
    """
    return _ERA_MARKER.sub(r"\1\2", text)


def normalize_spacing(text: str) -> str:
    """Collapse runs of whitespace and tighten spacing around punctuation."""
    text = re.sub(r"\s+", " ", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _SPACE_AFTER_OPEN.sub(r"\1", text)
    return text.strip()


def canonicalize(text: str, *, fold_letters: bool = False) -> str:
    """Return the canonical form of a fragment of Arabic financial text.

    :param text: Source text; may mix Arabic and Latin script.
    :param fold_letters: Also fold alef/ya/ta-marbuta variants. Lossy.
    :returns: Canonical text, safe to compare against another canonical form.
    """
    if not text:
        return ""
    out = unicodedata.normalize("NFKC", text)
    out = strip_invisibles(out)
    out = strip_diacritics(out)
    out = fold_numerals(out)
    if fold_letters:
        out = fold_letter_variants(out)
    out = normalize_spacing(out)
    return normalize_era_marker_spacing(out)


def canonicalize_markup(markup: str, *, fold_letters: bool = False) -> str:
    """Canonicalize the text nodes of an HTML/markdown string, leaving tags alone.

    Table metrics parse the markup that surrounds the text, so rewriting a tag
    would change the table's structure rather than its content. Only the spans
    between tags are touched.
    """
    if not markup:
        return ""
    parts = _TAG_SPLIT.split(markup)
    for i, part in enumerate(parts):
        if part.startswith("<") and part.endswith(">"):
            continue
        parts[i] = canonicalize(part, fold_letters=fold_letters)
    return "".join(parts)
