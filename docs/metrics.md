# Reading the ArabicFinBench tables

Every number here answers one question about one system on one document. None
of them is a summary of the others, and there is deliberately no combined
score — the failures they describe are different in kind, and averaging them
would rank a system that produces confident wrong figures above one that reads
imperfectly but never miscalculates.

---

## The three passes: `raw`, `text`, `struct`

Most metrics are reported three times, and the difference between the three is
usually more informative than any one of them.

**`raw`** is what the upstream metric produces with no normalisation at all —
the number an ExtractBench-style leaderboard would publish. It compares cell
text literally, so a system that writes `839,821` where the ground truth writes
`٨٣٩,٨٢١` is scored wrong for a number it read correctly.

**`text`** folds transcription conventions on *both* sides: digit script,
thousands separators, bracketed negatives, diacritics, invisible bidi marks,
spacing. These change how a value is written, never which value it is.

**`struct`** additionally folds table-shape conventions: section-header rows,
blank spacer rows, and column direction. An RTL page yields a label-first
array from one faithful reader and label-last from another; both are correct
readings, and without this they score as though one of them misread the page.

**`struct` is the ArabicFinBench P score.** `raw` is shown beside it because
hiding it would conceal how much of a system's apparent quality was
convention rather than reading.

---

## Table 1 — table metrics

This table asks: *did the system reconstruct the tables?* It works at the level
of whole rows and whole tables.

### `TRM` (Table Record Match)

Treats each table row as a record and finds the best one-to-one pairing between
ground-truth rows and predicted rows, then scores how well the paired rows
match. Because it matches records rather than grid positions, it tolerates a
system that emits rows in a different order but still penalises wrong values.
It is the primary P number. **Higher is better; 1.0 means every row was
recovered with its values intact.**

### `GriTS struct` (Grid Table Similarity)

Compares the tables as *grids* — cell by cell, in position. It is stricter than
TRM about layout: a system that gets every value right but shifts them one
column over scores well on TRM and badly on GriTS. Read the two together: TRM
high with GriTS low means the content is there but the structure is wrong.
**Higher is better.**

### `raw→canon Δ`

The movement from `raw` to `struct`, and the single most diagnostic column in
the table. A value near zero means the system already writes the way the
annotator does, so its raw score was honest. A large value means the raw score
was substantially about transcription convention rather than reading quality.
**This is not a quality score** — a system with a large Δ is not worse, it
simply was being penalised for a convention, and the Δ tells you how much.

### `tables` (paired / emitted)

How many tables the system produced, and how many of those paired with a
ground-truth table. `5/5` means it found the five tables that exist. `5/10`
means it emitted ten, of which five paired — it fragmented the page, and the
five unmatched fragments are content that exists but cannot be scored against
anything. **Watch the second number: a system that splits one table into six
has lost the row-to-value relationships even if every character is correct.**

### `status`

How the result was obtained. `api` means it ran through the provider's API here,
with cost, latency and version recorded. `hand-imported` means the output was
exported by hand from a console — usable for comparison, but its mode and cost
are not verifiable, so it is refused from any published leaderboard.

---

## Table 2 — cell metrics and null correctness

This table asks: *did the system read the individual figures, and did it invent
or drop anything?* Table 1 scores a wrong cell and an absent cell identically;
this table separates them, which is the distinction that matters most for
financial documents.

### `coverage`

The fraction of ground-truth cells for which the system produced *anything at
all*, right or wrong. It is the silent-drop detector. A cell a system never
attempted was previously visible only through recall, mixed together with cells
it attempted and got wrong — but declining to read and misreading are different
failures. **Read it against numeric exactness: high coverage with low exactness
means the system tried and misread; low coverage means it did not try.**

### `numeric exact`

Of the cells that hold a figure, the fraction the system got exactly right,
compared after digit script is folded so `٨٦٦,٠٨٣` and `866,083` count as
agreement. Labels are excluded entirely — getting every Arabic label wrong
cannot move this number, and getting every figure wrong cannot be hidden by
correct labels. **This is the number to quote when someone asks whether the
figures can be trusted.**

### `digit CER` (Character Error Rate, digits only)

The edit distance between the ground truth's digits and the system's, over
numeric cells only, divided by the number of ground-truth digits. It exists
because TRM scores one wrong digit in a long figure as a total miss — the same
penalty as an unreadable cell — and for finance those are not the same event.
**Lower is better.** A system can have a low CER and a poor exact-match rate:
that means one stray digit spread across many figures, which is materially
different from a few figures being badly wrong.

### `null acc`, `fabricated`, `dropped`, `judged`

These describe cells where either side states no value. `judged` is how many
such cells there were; the other three split the outcomes.

**`fabricated`** is the share of genuinely empty cells that the system filled
in with a value. This is the most dangerous failure in the set: an empty cell
that becomes `0` corrupts every sum downstream of it, silently, and still
reconciles if the system is consistent about it — which is why the extraction
prompt forbids it.

**`dropped`** is the reverse: real printed figures the system reported as
empty. Less insidious than fabrication because it is visible, but it destroys
data that was on the page.

**`null acc`** is the share of null-involving cells handled correctly. Read the
two directional rates rather than this single number — two systems can have
similar accuracy while erring in opposite directions, and for a financial
pipeline those are not interchangeable. Note that a printed `0` is **not** null:
an empty cell and a stated zero are different claims about the page.

---

## Diagnostics

### `script fidelity`

The fraction of the system's digit runs written in the same script as the page,
measured on the **raw** output before any normalisation. Canon deliberately
makes value scores independent of script, so this column is where the credit
for preserving `٨٣٩,٨٢١` as printed lives instead. **It is never folded into a
P score** — it describes faithfulness to the page's presentation, not accuracy.
Read it beside `raw→canon Δ`: a system with fidelity near 1.0 will have a Δ
near zero, because it needed no folding.

### `$/page` and `latency`

Cost per page and wall-clock time for the run, taken from the harness's own
records. They are reported because a benchmark that ignores them implies the
most accurate system is the right choice, which is rarely true — the table
regularly shows a system that is several times cheaper and an order of
magnitude faster while giving up a few points of accuracy.

---

## What is not here

**F (arithmetic)** — whether the extracted figures actually add up — is
implemented and tested but not reported for this document, because no
arithmetic rules have been authored for it yet. That is ground-truth work,
not a missing capability.

**A combined score** does not exist and cannot be produced: the generator
raises rather than emitting one, and CI rejects any table with an `overall`
column. See [fairness.md](fairness.md) guard 10 for why.
