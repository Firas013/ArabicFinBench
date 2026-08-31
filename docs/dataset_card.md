---
# Hugging Face dataset card template for ArabicFinBench.
# Proposed dataset id: <ORG>/ArabicFinBench
pretty_name: ArabicFinBench
license: apache-2.0
language:
  - ar
task_categories:
  - question-answering
  - table-question-answering
tags:
  - finance
  - arabic
  - document-understanding
  - information-extraction
  - benchmark
annotations_creators:
  - expert-generated
source_datasets:
  - original
---

# Dataset Card for ArabicFinBench

> **Template.** Bracketed `<...>` fields are unfilled. No corpus has been
> released yet; nothing in this card should be read as a published result.

- **Proposed dataset id:** `<ORG>/ArabicFinBench`
- **Repository:** https://github.com/<ORG>/arabicfinbench
- **Upstream harness:** [ExtractBench](https://github.com/run-llama/ExtractBench) (Apache-2.0)
- **Point of contact:** `<CONTACT>`

## Dataset summary

ArabicFinBench evaluates Arabic financial-document understanding. Systems are
scored on three axes that are **always reported separately** and never combined:

| Axis | Name | What it measures |
| --- | --- | --- |
| **P** | Parse | Document → structured text and layout fidelity |
| **E** | Extract | Schema-guided field extraction correctness |
| **F** | Finance | Financial-reasoning correctness (arithmetic, concept mapping) |

Consumers of this dataset are asked to preserve the P/E/F split when reporting.
A single averaged "ArabicFinBench score" misrepresents the benchmark, because a
system that extracts perfectly but miscalculates totals is not partially correct
— it is confidently wrong in the way that matters most for financial use.

## Supported tasks

`<TASKS>` — to be specified alongside the P/E/F dimension definitions.

## Languages

Arabic (`ar`). `<Script, dialect, and register coverage to be documented.>`

## Dataset structure

`<Splits, fields, and per-axis annotation schema to be documented.>`

Ground truth is versioned in the repository under `arabicfinbench/gt/`. Source
documents are distributed here rather than in git, because per-publisher
redistribution terms cannot be represented by a single repository licence.

## Data collection and provenance

`<Sources, collection window, and per-source redistribution terms.>`

## Annotation

`<Annotator expertise, guidelines, adjudication process, and inter-annotator
agreement.>`

## Personal and sensitive information

`<Screening process for PII in filings.>`

## Limitations and out-of-scope use

This dataset does **not** support claims about:

- general Arabic language ability (translation, dialogue, dialect handling);
- financial judgment, valuation, or advice quality;
- production readiness, or fitness for audit, regulatory, or compliance use;
- exhaustive coverage of Arabic scripts, dialects, regional accounting
  conventions, or reporting standards across jurisdictions.

Score differences without reported confidence intervals are not evidence of a
meaningful difference between systems.

## Licensing

Benchmark code and annotations: Apache-2.0. Source documents remain under their
original terms; see per-source provenance above.

## Citation

See `CITATION.cff` in the repository. Please cite ExtractBench as the upstream
harness in addition to ArabicFinBench.
