# data/

Local materialization point for source corpora. **Contents are intentionally
untracked.**

Upstream ExtractBench ignores `data/` at any depth. ArabicFinBench keeps that
behaviour for the corpus itself and tracks only this README and `.gitkeep`, so
the documented layout survives a fresh clone without committing source
documents.

Rationale: Arabic financial filings carry per-publisher redistribution terms
that a single repository licence cannot represent. Documents are distributed
via the Hugging Face dataset (see `docs/dataset_card.md`); ground truth and
annotations live in `arabicfinbench/gt/` and are tracked normally.

Nothing here is used for scoring until the corpus is populated.
