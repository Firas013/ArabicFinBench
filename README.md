# ArabicFinBench

An evaluation benchmark for Arabic financial-document understanding, built as a
fork of [ExtractBench](https://github.com/run-llama/ExtractBench).

> **Status: pre-release scaffolding. Nothing is scored yet.**
> The harness runs and the environment is reproducible, but no ArabicFinBench
> corpus, ground truth, or results exist in this repository. Any numbers you
> find under `docs/` are inherited ExtractBench results and are **not**
> ArabicFinBench results.

## Provenance

ArabicFinBench is a fork, not a reimplementation. The parsing, extraction, and
evaluation machinery is ExtractBench's, licensed under Apache-2.0 and retained
with its history intact. ArabicFinBench adds an Arabic financial-reasoning
overlay on top.

- Upstream: `run-llama/ExtractBench` (Apache-2.0)
- Upstream README, preserved verbatim: [docs/UPSTREAM_README.md](docs/UPSTREAM_README.md)
- Modifications are enumerated in [NOTICE](NOTICE), per Apache-2.0 §4(b)

## The P/E/F reporting rule

ArabicFinBench reports **three scores, always separately**:

| Axis | Name | What it measures |
| --- | --- | --- |
| **P** | Parse | Fidelity of document → structured text and layout |
| **E** | Extract | Schema-guided field extraction correctness |
| **F** | Finance | Financial-reasoning correctness (arithmetic, concept mapping) |

**These are never combined into a single ArabicFinBench score.** Not averaged,
not weighted, not reduced to a headline number — in this README, in
`leaderboard`-style outputs, or in any published comparison.

The reason is that the three axes fail in qualitatively different ways, and
collapsing them hides exactly what a reader needs to know. A system that parses
an Arabic balance sheet cleanly and extracts every field correctly, but computes
a wrong total, is not "90% correct" — it is a system that produces confident,
well-formed, wrong financial figures. Averaging would rank it above a system
that parses imperfectly but never miscalculates, which inverts the ordering that
matters for financial use. Any comparison that quotes one ArabicFinBench number
is misusing the benchmark.

## Canonicalisation

Arabic financial documents are transcribed inconsistently in ways that carry no
information. `٨٣٩,٨٢١` and `839,821` are the same number; `٢٠٢٤ م` and `٢٠٢٤م`
are the same year; a bidi control character is invisible. Upstream's table
metrics compare cell text literally, so these differences are scored as errors.

`arabicfinbench/canon/` defines the canonical forms, and they are applied to
**both the ground truth and the system output** before comparison — never to
the ground truth alone, which would move the bias rather than remove it.

Text is not the only axis on which two correct readings disagree. A section
header — `الموجودات المتداولة` — is a sparse row to one system and a full-width
`colspan` cell to another. Neither is a record, but they occupy different
numbers of grid cells, so every row below one scores as a miss on a positional
metric. `canon/structure.py` lifts section rows out of the grid on both sides
and records them as `Section(label, before_row)`, keeping them available as the
grouping context that concept tagging needs.

Three tiers, kept separate because they differ in risk:

| Tier | Transforms | Default |
| --- | --- | --- |
| Representational | digits, separators, diacritics, tatweel, bidi/zero-width marks, punctuation and era-marker spacing | on |
| Structural | section-header rows, blank spacer rows | on |
| Orthographic | alef / ya / ta-marbuta variants | off — lossy, opt in with `--fold-letters` |

`scripts/afb_score_parse.py` reports all three passes side by side — `raw`,
`text`, `struct`. Each is defensible and they differ substantially; quoting one
without the others hides which a claim rests on.

It also prints, per table, `rows_gt / rows_pred / sections / blanks`. When row
counts still disagree after section removal, the ground truth and the system are
modelling the table differently, and no text rule will close it — the next
convention mismatch shows up as a number rather than a debugging session.

```bash
python scripts/afb_gt_to_sidecar.py <gt>.json <doc>.pdf   # GT -> harness sidecar
extract-bench run <pipeline> --input_dir <dir>            # inference + raw score
python scripts/afb_score_parse.py --pipeline <pipeline> --input-dir <dir>
```

Canonicalisation raises scores, so it is worth stating what it is not: it
normalises *representation*, never value. It will not turn a misread digit into
a correct one, and a system that reports the wrong figure scores wrong under
canon exactly as it does raw.

## What ArabicFinBench does not claim

- **It is not a general Arabic NLP benchmark.** Performance here says nothing
  about Arabic translation, dialogue, summarization, or dialect handling.
- **It is not a measure of financial judgment.** It scores extraction and
  arithmetic against ground truth. It does not evaluate financial advice,
  valuation, or interpretation.
- **It does not certify production readiness**, correctness on unseen filings,
  or fitness for audit, regulatory, or compliance use.
- **It does not claim exhaustive coverage** of Arabic scripts, dialects,
  regional accounting conventions, or reporting standards across jurisdictions.
- **Rankings are not significance-tested.** Score differences without reported
  confidence intervals should not be read as meaningful differences between
  systems.
- **It is not a claim about upstream ExtractBench.** ArabicFinBench results do
  not transfer to ExtractBench's leaderboard, and vice versa.

## Repository layout

Additions sit alongside the upstream tree rather than replacing it:

```
arabicfinbench/
  canon/                  # canonical forms (implemented)
  concepts/               # financial concept definitions (stub)
  dimensions/arithmetic/  # arithmetic evaluation dimension (stub)
  gt/                     # ground truth (tracked)
  data/                   # local corpora (untracked; see data/README.md)
scripts/afb_gt_to_sidecar.py   # raw GT -> harness sidecar + expected_markdown
scripts/afb_score_parse.py     # raw vs canonical P scoring
tests/arabicfinbench/     # tests for the overlay
src/extract_bench/        # upstream harness, unmodified
```

`arabicfinbench/` is an importable package (declared in hatchling's
`packages` and shipped in the wheel) - `canon/` and `dimensions/arithmetic/`
are code the scorer imports, not data. `gt/` and `data/` remain data-only.

Upstream's package name and import paths are deliberately left alone so that
upstream changes can still be merged.

## Environment

Requires **Python ≥3.12** (upstream constraint) and **Node ≥14** for the HTML
report assets. Both are pinned rather than assumed.

```bash
uv sync --extra dev --python 3.12    # add --extra runners for provider integrations
uv run pytest -q
bash scripts/install-hooks.sh        # refuse commits of corpus documents
```

`install-hooks.sh` points `core.hooksPath` at the tracked `scripts/hooks/`, so
hook changes reach everyone on their next pull. The same rule runs in CI, which
does not depend on a hook being installed — or on its executable bit surviving
an edit from a Windows checkout.

Node version is pinned in `.node-version` (20.19.5). Node older than 14 fails
six report-asset tests with `SyntaxError: Unexpected token '?'` — the report JS
uses nullish coalescing. This is an environment problem, not a code problem.

## Licence and citation

Apache-2.0, inherited from ExtractBench. See [LICENSE](LICENSE) and
[NOTICE](NOTICE). If you use ArabicFinBench, cite it via
[CITATION.cff](CITATION.cff) — and cite ExtractBench as the upstream harness.

## Note on upstream tooling

`scripts/update_readme.py` regenerates leaderboard tables from a root
`leaderboard.csv`. ArabicFinBench has no leaderboard yet, and upstream's CSV was
moved to `docs/upstream_leaderboard.csv` to keep ExtractBench numbers from being
read as ArabicFinBench results. That script will therefore error until it is
rewired; this is intentional and preferable to it silently publishing the wrong
numbers.
