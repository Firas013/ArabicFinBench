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
  canon/                  # canonical forms
  concepts/               # financial concept definitions
  dimensions/arithmetic/  # arithmetic evaluation dimension
  gt/                     # ground truth (tracked)
  data/                   # local corpora (untracked; see data/README.md)
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
```

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
