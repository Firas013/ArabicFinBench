"""Canonical forms for comparing Arabic financial text.

Two systems can transcribe the same balance-sheet cell in ways that differ in
every byte and in no fact: ``٨٣٩,٨٢١`` and ``839,821`` are the same number, and
``٢٠٢٣ م`` and ``٢٠٢٣م`` are the same year. Scoring those as mismatches measures
typography, not document understanding, and it does so in a direction that
flatters whichever system happens to share the ground truth's conventions.

Canonicalisation is therefore applied to *both* sides before any comparison —
never to the ground truth alone, which would merely move the bias rather than
remove it. The scoring layer (:mod:`arabicfinbench.scoring`) enforces this
structurally: it canonicalises internally and exposes no way to canonicalise one
side only.

Every transform here is a **named rule**. Application through
:func:`canonicalize_traced` reports which rules actually changed the input, so a
scored result can say not just "canon was applied" but which conventions each
side needed folding — a side whose raw output needs no folding shares the
annotator's conventions, and that fact belongs in the report, not in the score.

The transforms are split into two tiers:

default (representational)
    Digits, separators, parenthesised negatives, diacritics, invisible
    directional marks, spacing around punctuation and era markers. These change
    how a value is written, never which value it is.

``fold_letters=True`` (orthographic)
    Additionally folds alef/ya/ta-marbuta variants. Standard for Arabic
    retrieval but genuinely lossy: distinct spellings can merge. Opt-in —
    measured at +0.0007 GriTS on the first benchmark document, which is the
    argument for leaving it off.

One deliberate non-rule: a **missing** inter-word space is never repaired.
``كلمةكلمة`` and ``كلمة كلمة`` differ by a real transcription edit; collapsing
them would erase a model error, not a convention.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

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

# Harakat and other combining marks, written as explicit escapes: literal
# Arabic ranges are unreadable and once produced a class that silently spanned
# the digit block U+0660–0669, deleting every Arabic-Indic digit before the
# numeral fold could see one. U+0670 (superscript alef) is included; the ranges
# deliberately exclude U+0660–066F (digits and separators).
_DIACRITICS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed]")

# Tatweel is a justification glyph with no phonetic or semantic content.
_TATWEEL = re.compile(r"ـ+")

# Bidi controls and zero-width characters are invisible, so a mismatch caused by
# one is always an artefact.
_INVISIBLE = re.compile("[\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")

# Punctuation that should not carry a leading space, in both scripts.
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,،.؛;:!؟?%\)\]])")
_SPACE_AFTER_OPEN = re.compile(r"([\(\[])\s+")

# Era markers: ``م`` (ميلادي, Gregorian) and ``ه`` (هجري, Hijri) trail a year with
# optional space — ``٢٠٢٤ م`` and ``٢٠٢٤م`` are the same year. The tatweel in the
# common ``هـ`` spelling is already gone by the time this runs. The trailing
# ``(?!\w)`` keeps the rule from biting into a longer word that merely starts
# with one of these letters.
_ERA_MARKER = re.compile(r"(\d)\s+([مه])(?!\w)")

# Accounting negatives: a parenthesised pure numeral means minus. Runs after
# digit folding, so only ASCII digits/separators appear inside. Parentheses
# around words — ``( شركة ذات مسؤولية محدودة )`` — never match.
_PAREN_NEGATIVE = re.compile(r"\(\s*(\d[\d,.]*)\s*\)")

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


def nfkc(text: str) -> str:
    """NFKC-normalise, folding Arabic presentation forms to base letters."""
    return unicodedata.normalize("NFKC", text)


def fold_numerals(text: str) -> str:
    """Map Arabic-Indic digits and Arabic separators to their ASCII forms."""
    return text.translate(_NUMERIC_MAP)


def fold_paren_negatives(text: str) -> str:
    """Rewrite accounting negatives ``(1,000)`` as ``-1,000``.

    A bracketed figure and a minus sign are the same value in two typesetting
    traditions; scoring them apart penalises a convention.
    """
    return _PAREN_NEGATIVE.sub(r"-\1", text)


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
    """Collapse runs of whitespace and tighten spacing around punctuation.

    Only *extra* space is removed. A missing space between words is a
    transcription edit and stays one.
    """
    text = re.sub(r"\s+", " ", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _SPACE_AFTER_OPEN.sub(r"\1", text)
    return text.strip()


# The pipeline, in application order. Order matters and is part of the canon
# version: paren negatives need folded digits; era markers need collapsed
# whitespace to already be single spaces.
_BASE_RULES: tuple[tuple[str, Callable[[str], str]], ...] = (
    ("text/nfkc", nfkc),
    ("text/strip_invisibles", strip_invisibles),
    ("text/strip_diacritics", strip_diacritics),
    ("text/fold_numerals", fold_numerals),
    ("text/fold_paren_negatives", fold_paren_negatives),
    ("text/normalize_spacing", normalize_spacing),
    ("text/era_marker_spacing", normalize_era_marker_spacing),
)

_LETTER_RULE: tuple[str, Callable[[str], str]] = ("text/fold_letter_variants", fold_letter_variants)


def rules(*, fold_letters: bool = False) -> tuple[tuple[str, Callable[[str], str]], ...]:
    """The active rule pipeline, in order."""
    if not fold_letters:
        return _BASE_RULES
    # Letter folding slots in after numeral folding, before spacing, so the era
    # marker rule sees folded ``ه`` forms consistently.
    out = list(_BASE_RULES)
    out.insert(5, _LETTER_RULE)
    return tuple(out)


def canonicalize_traced(text: str, *, fold_letters: bool = False) -> tuple[str, tuple[str, ...]]:
    """Canonicalize a text fragment, reporting which named rules changed it."""
    if not text:
        return "", ()
    fired: list[str] = []
    out = text
    for name, fn in rules(fold_letters=fold_letters):
        new = fn(out)
        if new != out:
            fired.append(name)
        out = new
    return out, tuple(fired)


def canonicalize(text: str, *, fold_letters: bool = False) -> str:
    """Return the canonical form of a fragment of Arabic financial text."""
    return canonicalize_traced(text, fold_letters=fold_letters)[0]


def canonicalize_markup_traced(markup: str, *, fold_letters: bool = False) -> tuple[str, tuple[str, ...]]:
    """Canonicalize the text nodes of an HTML/markdown string, leaving tags alone.

    Table metrics parse the markup that surrounds the text, so rewriting a tag
    would change the table's structure rather than its content. Only the spans
    between tags are touched. Returns the canonical markup and the union of
    rule names that fired anywhere in the document.
    """
    if not markup:
        return "", ()
    fired: set[str] = set()
    parts = _TAG_SPLIT.split(markup)
    for i, part in enumerate(parts):
        if part.startswith("<") and part.endswith(">"):
            continue
        parts[i], part_fired = canonicalize_traced(part, fold_letters=fold_letters)
        fired.update(part_fired)
    return "".join(parts), tuple(sorted(fired))


def canonicalize_markup(markup: str, *, fold_letters: bool = False) -> str:
    """Canonicalize markup text nodes; see :func:`canonicalize_markup_traced`."""
    return canonicalize_markup_traced(markup, fold_letters=fold_letters)[0]
