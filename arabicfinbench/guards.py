"""Guards that make scoring failures loud, named, and attributable.

Each guard exists because a silent failure was observed to masquerade as a
model result. A benchmark that averages over garbage is not lenient, it is
wrong — and wrong in whichever direction the garbage happens to lean.
"""

from __future__ import annotations

import re

# UTF-8 Arabic read as Latin-1 turns every letter into a two-character pair
# whose first character is Ø (from bytes D8xx) or Ù (D9xx) — Latin letters that
# effectively never occur in genuine Arabic or English financial text. Ã and Â
# are the same artefact for Latin-1 supplement bytes. One such pair could
# conceivably be real text; a run of them cannot.
_MOJIBAKE_PAIR = re.compile("[\u00d8\u00d9\u00c3\u00c2][\u0080-\u00ff]")

# How many pairs it takes before the text is condemned. Three pairs is already
# vanishingly unlikely in genuine content and appears within the first word of
# actual mojibake.
_MOJIBAKE_THRESHOLD = 3


class MojibakeError(ValueError):
    """Prediction (or ground truth) text is a broken encoding round-trip.

    Scoring it would report a catastrophic parse failure that never happened —
    on the first Datalab hand-run, the mojibake copy of an output that actually
    read the page correctly would have scored ~0.
    """


class EmptyPredictionError(ValueError):
    """A prediction with no content reached a code path that needed some.

    Raised only where an empty prediction cannot be represented as a zero
    score; the scorer itself scores empties as zero and lists them, never
    raises, never drops.
    """


def mojibake_pairs(text: str) -> int:
    """Count Latin-1-mojibake character pairs in a string."""
    return len(_MOJIBAKE_PAIR.findall(text or ""))


def is_mojibake(text: str) -> bool:
    """Whether a string bears the UTF-8-as-Latin-1 signature."""
    return mojibake_pairs(text) >= _MOJIBAKE_THRESHOLD


def assert_clean_encoding(text: str, *, source: str) -> str:
    """Refuse mojibake before it can be scored.

    :param source: Where the text came from, for the error message —
        ``"prediction: datalab_web"`` or ``"ground truth: test_1/Test_1"``.
    :raises MojibakeError: with the source and pair count named.
    """
    pairs = mojibake_pairs(text)
    if pairs >= _MOJIBAKE_THRESHOLD:
        raise MojibakeError(
            f"{source}: {pairs} Latin-1 mojibake pairs detected "
            f"(e.g. UTF-8 Arabic decoded as Latin-1). Re-export or re-read the "
            f"content as UTF-8; scoring this would fabricate a parse failure."
        )
    return text
