# dataset/

The corpus: one directory per document, named `test_<n>/`.

```
dataset/test_6/
  Test_6.pdf          the filing.        NOT tracked — see gt/CONVENTIONS.md §6
  Test_6.json         the ground truth.  tracked. the only hand-authored file
  Test_6.md           expected_markdown. tracked, generated
  Test_6.test.json    harness sidecar.   tracked, generated
```

The stem must match the PDF, because the harness discovers a case by looking for
`<pdf_stem>.test.json` beside it. The directory name becomes the document id:
`dataset/test_6` is stored as `test_6/Test_6`.

**Filings are not tracked; annotations are.** The two get opposite treatment
deliberately. A filing carries redistribution terms this repository's licence
cannot represent, and git history is permanent — `.gitignore`, the pre-commit
hook and a CI step all refuse one. The ground truth *is* the annotation, and
tracking it is what lets someone clone this repository and re-score a system
without re-annotating anything.

Regenerate the two derived files after any change to a `.json`:

```bash
python scripts/afb_gt_to_sidecar.py dataset/test_6/Test_6.json dataset/test_6/Test_6.pdf
```

## Current contents

Documents are identified by id only. The issuers are deliberately not named
here: naming which filings are in the corpus is itself a disclosure, and the id
is all any part of the harness needs.

| | sector | period | pages | scan | digits | relations |
| --- | --- | --- | --- | --- | --- | --- |
| test_1 | manufacturing | FY2024 | 3 | no | Arabic-Indic | 16 |
| test_2 | consumer services | 9M 2022 | 5 | no | Arabic-Indic | 16 |
| test_3 | materials | Q3 2022 | 4 | **yes** | Arabic-Indic | — |
| test_4 | banking | H1 2022 | 7 | no | **Latin** | 3 |
| test_5 | food & beverage | 9M FY2022 | 5 | no | Arabic-Indic | 19 |
| test_6 | real estate | Dec 2022 | 11 | **yes** | Arabic-Indic | 27 |

**test_3 has no usable ground truth.** Its `Test_3.json` is a byte-identical copy
of test_4's and describes the wrong filing; its own document has never been
annotated. The directory is excluded from git rather than shipping an answer key
that answers a different question. It is the cheapest way to grow the corpus by
a document.

**test_6 is not tracked.** Its ground truth is confidential and excluded from
git; only its de-identified results remain in `results/scores.jsonl`.

`test_4` is the only Latin-digit filing and the only one on which script
fidelity separates the systems — the others are uniformly Arabic-Indic, where
every system scores near 1.0.

## Adding a document

See [docs/adding_a_document.md](../docs/adding_a_document.md) for the authoring
rules, and [gt/CONVENTIONS.md](../arabicfinbench/gt/CONVENTIONS.md) for why each
one exists.
