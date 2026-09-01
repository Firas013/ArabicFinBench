# Ground truth conventions

Rules for authoring ArabicFinBench ground truth. They exist because each one
was, at some point, ambiguous enough that two reasonable annotators would have
encoded the same page differently — and because a benchmark whose ground truth
is internally inconsistent measures its own annotation noise.

Where a rule has a matching canonical form in `arabicfinbench/canon/`, that is
noted. **Canon is not a licence to be inconsistent.** It removes differences
between the ground truth and a *system*; it cannot remove differences between
one ground-truth document and another, and it does not repair a file that
contradicts itself.

## 1. Column order — one direction per document, stated

**Rule: encode cells in visual left-to-right order, exactly as the page renders,
and use the same direction for every table in a document.**

Arabic financial statements are laid out right-to-left, so the row label is
normally the *rightmost* column and therefore the **last** element of a row
array. Comparative year columns run to its left.

```json
["٨٣٩,٨٢١", "٨٦٦,٠٨٣", "", "نقد وأرصدة لدى البنوك"]
   2023        2024     note        label (rightmost on the page)
```

There is no canonical form for this. A grid metric compares cell positions, so
a reversed table scores near zero however well it was read, and no text rule can
detect the reversal — a reversed row is a valid row.

This rule is not hypothetical. In the first document authored for the benchmark,
table 0 was label-last while tables 2, 3 and 4 were the reverse. Against an
identical parse, positional cell agreement was 98% for the first and 0–33% for
the others. Nothing was misread; the ground truth simply disagreed with itself.

**Check before committing:** take any two tables in the document and confirm the
row label sits at the same end of the array in both.

## 2. Section headers — encode them, sparsely

**Rule: encode a section header as its own row, with the label in the label
column and every other cell empty.**

```json
["", "", "", "الموجودات المتداولة"]
```

Do not merge a section label into the header row, and do not omit it. It is
grouping context that concept tagging needs, and it carries the distinction
between current and non-current assets that the Finance axis depends on.

Canon: `strip_sections` lifts these out of the grid before Parse metrics run,
recording each as `Section(label, before_row)`. A system that emits the same
header as a full-width `colspan` cell canonicalises to the identical result, so
both encodings score alike — that is the point of the rule, not a reason to be
careless with it.

The same canonical form treats *any* row with exactly one non-empty cell as a
section. A genuine single-value row — a lone total with no label — is therefore
indistinguishable from a section header. Give totals a label.

## 3. Blank rows — do not encode them

**Rule: a row with no content in any cell is not part of the table.**

Parsers emit blank rows as spacers around section breaks; ground truth should
not. Canon drops them on both sides and reports the count per table, so a run
where they appear only on one side is visible rather than silent.

## 4. Numerals and text — write what the page shows

**Rule: transcribe verbatim. Do not normalise while annotating.**

Keep Arabic-Indic digits (`٨٣٩,٨٢١`) if the page uses them, keep the spacing
around era markers, keep the punctuation. Canon folds all of this at scoring
time, applied to the ground truth and the system output alike.

Normalising by hand during annotation is worse than useless: it is silent,
inconsistent between annotators, and it destroys the record of what the document
actually said.

Canon: `canonicalize` (numerals, separators, diacritics, tatweel, bidi and
zero-width marks, punctuation and era-marker spacing).

## 5. Ambiguous glyphs — transcribe the glyph, flag the cell

**Rule: where a character is genuinely ambiguous, record what is on the page and
note the cell.**

Arabic `١` (one) and `أ` (alef) are near-identical in some financial typefaces.
A note reference of `٧/١` and one of `٧/أ` are different references, and the
difference is invisible to canon — it will be scored, correctly, as a
disagreement. If the page cannot be resolved with confidence, the cell is a
ground-truth defect and should be fixed or the document dropped, not guessed.

## 6. Corpus documents stay out of git

**Rule: no source document is committed to this repository.**

Arabic financial filings carry per-publisher redistribution terms that this
repository's licence cannot represent, and git history is permanent. Documents
are distributed through the Hugging Face dataset; only ground truth and
annotations are tracked here.

This is enforced by `scripts/hooks/pre-commit` and by CI, not by good
intentions. See `arabicfinbench/data/README.md`.

A public fixture must come from a filing with confirmed redistribution rights —
a Tadawul-published statement, for instance. A redacted private document is
still a private document.
