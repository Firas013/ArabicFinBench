"""Run provenance: what a leaderboard row must be able to prove about itself.

The unfairness this guards: a number whose origin cannot be reconstructed —
which adapter, which model version, which mode, which canon, on which page
images, at what cost, how many seeds — is not a benchmark result; it is a
rumour with decimals. Every field here is required, and the generator rejects a
row missing any of them with a named error.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, fields
from pathlib import Path

# Prompt-free adapters (parse APIs with no instruction channel) record this
# instead of a hash. It is an explicit statement, not an omission.
NO_PROMPT = "none"


class MissingProvenanceError(ValueError):
    """A leaderboard row is missing required provenance fields, listed by name."""

    def __init__(self, adapter: str, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"row '{adapter}' rejected: missing provenance field(s): {', '.join(missing)}")


class HandImportedResultError(ValueError):
    """A hand-imported result reached the leaderboard path.

    Hand imports (afb_import_datalab.py) are welcome in the dev report; a
    leaderboard row must come from the API adapter in a named mode, or the
    mode, version, cost, and latency columns are guesses.
    """


class ExternalReportError(ValueError):
    """Scores were reported from elsewhere rather than re-derived here.

    A hand-imported result still carries the system's actual output, so its
    scores are computed by this repository's scorer at this canon version. An
    externally reported number carries nothing: it cannot be re-derived, its
    canon version cannot be checked, and page-image hashes cannot be computed,
    so there is no way to know it describes the same document under the same
    rules. It is recorded and labelled in the dev report; the leaderboard needs
    the run.
    """


@dataclass(frozen=True)
class Provenance:
    """Everything a leaderboard row must carry. Empty means missing."""

    adapter: str = ""
    model_version: str = ""
    mode: str = ""
    canon_version: str = ""
    cost_per_page_usd: float | None = None
    median_latency_ms: float | None = None
    seed_count: int | None = None
    run_timestamp: str = ""
    page_image_hashes: tuple[str, ...] = field(default_factory=tuple)
    prompt_sha256: str = ""  # NO_PROMPT for prompt-free adapters — stated, not omitted
    hand_imported: bool = False
    reference_implementation: bool = False
    external_report: bool = False
    reported_by: str = ""  # who reported it and from where, when external_report

    # Flags and attribution describe the row; they are not fields it must prove.
    _NON_REQUIRED = ("hand_imported", "reference_implementation", "external_report", "reported_by")

    def missing_fields(self) -> list[str]:
        """The required fields this row cannot prove."""
        missing: list[str] = []
        for f in fields(self):
            if f.name in self._NON_REQUIRED:
                continue
            value = getattr(self, f.name)
            if value is None or value == "" or value == ():
                missing.append(f.name)
        return missing

    def validate_for_leaderboard(self) -> None:
        """Reject the row unless every required field is present and it came
        through the API adapter path.

        :raises HandImportedResultError: for hand-imported results.
        :raises MissingProvenanceError: listing every absent field by name.
        """
        if self.external_report:
            raise ExternalReportError(
                f"row '{self.adapter or '<unnamed>'}' carries externally reported scores"
                f"{f' (reported by {self.reported_by})' if self.reported_by else ''}; "
                f"they cannot be re-derived at canon {self.canon_version or '<unknown>'}, "
                f"so the row is recorded in the dev report only. Re-run the system here "
                f"to produce a leaderboard row."
            )
        if self.hand_imported:
            raise HandImportedResultError(
                f"row '{self.adapter or '<unnamed>'}' is hand-imported; allowed in the dev "
                f"report, blocked from the leaderboard. Re-run through the API adapter "
                f"in a named mode."
            )
        missing = self.missing_fields()
        if missing:
            raise MissingProvenanceError(self.adapter or "<unnamed>", missing)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_image_hashes(pdf_path: Path, *, dpi: int = 150) -> tuple[str, ...]:
    """One sha256 per page, over deterministically rendered page rasters.

    Hashing the rendered pixels rather than the container ties a result to what
    the models actually saw: a re-saved PDF with identical pages keeps its
    hashes; a swapped page does not.
    """
    import pymupdf  # heavy import kept local

    hashes: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            pixmap = page.get_pixmap(dpi=dpi)
            hashes.append(sha256_hex(pixmap.samples))
    return tuple(hashes)
