# Fairness guards

The principle: **every point a model loses must be attributable to the model —
not to a convention, the harness, or the annotator.** Each guard below is
enforced code with tests, not policy text, and each one exists because the
unfairness it prevents was actually observed. File references are to the
enforcing code; every guard has tests in `tests/arabicfinbench/` that fail
without it.

Guards 1–10 were derived from the first document (Test_1, a Saudi financial
statement). Expanding to five documents found three more failures of the same
principle, each now fixed and regression-tested:

- **Table pairing.** The cell metrics compared ground-truth table *i* against
  prediction table *i* by position, while GriTS matched them properly with a
  Hungarian assignment. A prediction that split one table offset every table
  after it. On the 11-page scan this reported `numeric_exact = 0.0000` for every
  system while 83% of the ground truth's figures were present verbatim in their
  output. Fixed by reusing GriTS's own pairing.
- **Ragged tables.** Column ordering declined on uneven row widths, so it fired
  on the rectangular ground truth and skipped a prediction with one short row,
  leaving the sides in different column frames. Canon was symmetric by
  construction and asymmetric in effect. Short rows are now padded.
- **Empty predictions ranked as measurements.** A system returning nothing was
  stored as a normal row scoring 0.0000, which reads as "transcribes nothing
  correctly" rather than "returned nothing". Now forced to `failed`.
- **Rows and columns read off by index.** Table pairing was fixed first, but
  inside a paired table the cell metrics still assumed row *i* meant the same
  row on both sides. One extra header row shifted everything beneath it. Now
  aligned with GriTS's own row and column maps.
- **Colspans refusing the table.** Column ordering declined on any residual
  span, which — like the ragged case — fired on the colspan-free ground truth
  and skipped the prediction. Spans are now expanded into the grid positions
  they occupy.

The last two were the same asymmetry as the ragged-row case, at different
depths, and correcting them moved the E and F axes substantially: digit error
fell by 0.33 on average across 41 of 43 rows, and arithmetic consistency rose by
0.47 across 29. The P table metrics barely moved (9 of 43, +0.03), which is the
expected signature — they always did their own alignment; it was the cell
metrics that were reading the wrong cells.

## 1. Symmetric canonicalisation — `arabicfinbench/canon/`, `arabicfinbench/scoring.py`

Two faithful transcriptions of the same page can differ in every byte:
`٨٣٩,٨٢١` vs `839,821`, `(٤١٥,٦٥٩)` vs `-415,659`, a section header as a sparse
row vs a full-width colspan, label-first vs label-last column order. Scoring
those as errors measures typography, in whichever direction flatters the system
that shares the annotator's habits. Canon folds them — text tier and structure
tier, every rule named and the canon version stamped into every result — and
`score_document()` applies it to ground truth and prediction inside the same
call, with **no parameter to canonicalise one side only**: the biased comparison
is unrepresentable, and two tests each kill one one-sided variant. Evidence:
on Test_1, canon moved LlamaParse's `grits_con` 0.4402 → 0.9194 without
touching a single cell value, and the lossy letter-folding tier stays off
because it was measured at +0.0007. A missing inter-word space is deliberately
*not* folded: that is a model error, and repairing it would erase one.

## 2. Script fidelity, reported separately — `arabicfinbench/scoring.py`

Canon folds digit script so values score fairly — which would silently erase
the credit due to a system that preserved `٨٣٩,٨٢١` exactly as printed.
`script_fidelity` is computed on the **raw** output (fraction of digit runs in
the page's script, page script taken from the verbatim ground truth), lives in
its own column, and is never folded into a P score. Evidence: Datalab 1.0000,
LlamaParse 0.2402 on Test_1 — which, beside the raw→struct delta, is the whole
rank-flip story in two numbers.

## 3. Raw next to canon, always — scorer, leaderboard generator

Every table shows `raw | text | struct` plus the per-model raw→struct delta.
The delta is a diagnostic: near zero means the model shares the annotator's
conventions; large means the raw number was substantially about conventions.
Evidence: Test_1's ranking **flips** between passes. On `table_record_match`,
raw says Mistral OCR 0.5732 vs LlamaParse 0.1511; canon says LlamaParse 0.9799
vs Mistral OCR 0.4086. LlamaParse gains +0.83 from canon, Mistral OCR loses
0.16. A leaderboard showing either pass alone would state a conclusion the other
pass contradicts. Both orderings are regression tests: a synthetic fixture
reproduces the mechanism in CI, and `TestRankFlipOnStoredResults` re-derives
them from the stored Test_1 results.

The flip is not confined to one document. Across the five-document corpus the
raw and struct passes name a different leader on **four of five** — they agree
only on `test_2`. Choosing a pass therefore chooses a winner most of the time,
which is why all three are always printed side by side.

## 4. One execution path — `arabicfinbench/provenance.py`, `scripts/afb_leaderboard.py`

A leaderboard row must carry: adapter, model version string, named mode, canon
version, cost per page, median latency, seed count, run timestamp, page-image
hashes (sha256 over deterministically rendered page rasters — tied to what the
models saw, not the PDF container), and prompt hash. A missing field rejects
the row with `MissingProvenanceError` naming it. Operator-stated fields (model
version, mode, seed count, sampled) live in tracked declarations under
`arabicfinbench/runs/` — a statement that gates admission cannot live only in
untracked scratch that `rm -rf output/` destroys. Evidence: Mistral was rejected
on first submission with `missing provenance field(s): mode`, because its
pipeline config carries `model` rather than `mode` and nothing was derivable;
the mode is now operator-stated with the reason recorded. Hand-imported results
(`afb_import_datalab.py` stamps them) appear in the dev report under that
label and are rejected from the leaderboard with `HandImportedResultError` —
their mode, cost, and latency would be guesses. Evidence: the Datalab web
export scored within 0.004 of the API run, and still does not qualify: mode
unknown. Datalab was re-run through its API adapter in the named `accurate`
mode for the admitted row.

### Test_1, three systems, all guards active

| `table_record_match` | raw | text | struct | Δ | fidelity | $/page | latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.3195 | 0.8149 | **0.9129** | +0.59 | 0.2402 | 0.0125 | 37.9 s |
| datalab_accurate | 0.7413 | 0.7488 | 0.7728 | +0.03 | 1.0000 | 0.0100 | 32.9 s |
| mistral_ocr_4 | 0.4509 | 0.4541 | 0.4685 | +0.02 | 1.0000 | 0.0040 | 2.7 s |

The delta column separates two situations that a single score conflates.
LlamaParse's raw number was substantially about numeral convention (+0.59);
Datalab's and Mistral's were not (+0.03, +0.02), and both preserve the page's
script exactly. So Mistral's low canon score is a **real** failure rather than an
artefact — and the per-table block says which one: it emitted 10 tables against a
ground truth of 5, decomposing the side-by-side note tables on page 3 into
single-column fragments and orphaning the row labels into free text. Column-order
canon reports `skip:too-small` on those fragments rather than inventing a
permutation, which is the refusal working as intended: the label↔value
association is gone, and no canonical form can restore it.

## 5. Fail loudly — `arabicfinbench/guards.py`, provider registry, scorer

Three observed silent failures, each now a named error. A missing transitive
dependency (PIL) once surfaced as "No provider registered for 'llamaparse'";
the registry now records provider import failures and names the original
exception in the miss error (the fork's one modification to `src/extract_bench`,
enumerated in NOTICE). The Datalab web export arrived once as UTF-8-read-as-
Latin-1; scoring it would have reported a catastrophic failure for a parse
that read the page correctly — mojibake now raises `MojibakeError` naming the
source, on either side, before any metric runs. An empty or failed prediction
scores **zero on every dimension, on the record**, listed by id — never
dropped, never averaged around; failed API calls are retried per upstream
policy, then scored zero and listed.

## 6. Nondeterminism — `arabicfinbench/determinism.py`

A sampled model's luckiest run beside a deterministic system's only run
misleads unless the table says which is which. Adapters register a determinism
class; `verify()` runs the fixture twice and byte-compares, upgrading to
*verified* or flagging *nondeterministic*. Flagged adapters must report 3 seeds
at temperature 0, mean and range per dimension (`SeedPolicyError` otherwise);
deterministic adapters run once and the row prints "runs once" so a
single-seed number is legible as such.

## 7. Contamination — `arabicfinbench/gt/contamination.py`, `scripts/afb_freeze.py`

`gt/splits.json`: dev (images and GT public) / test (images public, GT
withheld), validator refuses overlap. On freeze, `afb_freeze.py` publishes the
sha256 of every test GT file in the repo **before any leaderboard run** — the
hashes are the commitment, and a post-freeze edit is provable from git history
by anyone. `gt/training_exclusion.json` lists every document that ever touched
our own training sets (rec v6–v13, layout, V3; to be populated from the
inventories, and the manifest says so explicitly); `check_training_exclusion()`
makes "the test split is clean" a failing build rather than a footnote. The
reference implementation is labelled *"reference implementation, benchmark
authors"* on every leaderboard row it appears in.

## 8. Ground-truth integrity — `arabicfinbench/gt/integrity.py`

A benchmark whose ground truth is wrong scores its own annotation noise.
Every page passes schema validation (defects named, including convention
violations such as blank spacer rows and ragged tables) and an arithmetic
admission gate: every declared `total == sum(addends)` relation must reconcile
exactly — `Fraction`s, no float tolerance — and a page with no declared
relations is not admitted at all. Amounts parse by unambiguous shape
(`24,061,612` groups thousands; `٠,٠٢٥٨` is a decimal; `١٢٣٤,٥٦٧` is refused,
not guessed). Cells no relation reaches are tagged `arithmetic_blind` and
reported as their own line. The consensus rule flags any cell where ≥2
independent systems agree against the GT, for pixel re-verification, logged in
`gt/corrections.log.jsonl` — never silently edited. Evidence: the first real
run produced 22 entries, including mirrored value pairs on the equity table
(both systems outvoting the GT's column *direction* — the CONVENTIONS §1
defect, independently rediscovered) and the `٧/أ` note cell, where the log
records that the two systems disagree with the GT *and with each other*
(`٧/أ` vs `١/٧`) — a manual ambiguous-glyph flag, not a consensus.

## 9. Inclusion criteria, enforced — `arabicfinbench/leaderboard.py`

Inherited from upstream: public access, single-digit hours, no custom framework
changes. Added and enforced: the adapter must be registered in this public
repository (`UnknownAdapterError` otherwise — every row reproducible from
source), and the frozen prompt hash is a required provenance field. Prompt-free
parse APIs record the explicit value `"none"` — a statement, not an omission;
an empty prompt field rejects the row.

## 10. Never one number — `arabicfinbench/leaderboard.py`, CI

P, E, and F fail in qualitatively different ways; averaging them ranks a system
that produces confident, well-formed, wrong figures above one that never
miscalculates. `build_leaderboard(combined=True)` raises `CombinedScoreError`;
a metric named "overall" raises; emitted tables are asserted overall-free; and
CI greps every tracked leaderboard file for an overall column (upstream's
preserved CSV exempted by name — it is labelled as not being ArabicFinBench
results). Both directions verified: the current tree passes, and a probe file
with an `Overall` column is caught.
