# runs/

Operator-stated provenance, one file per adapter, **tracked**.

A leaderboard row must be able to prove its origin (see `docs/fairness.md`
guard 4). Most of that proof is derived mechanically from the harness's own
artefacts — mode from the pipeline config, cost and latency from the evaluation
CSV, timestamps from the result file, page-image hashes from the source PDF.
The rest is knowledge only the operator has: which model version answered,
how many seeds were run, whether the adapter samples.

Those statements live here rather than beside the run output, because
`output/` is untracked scratch: a declaration that gates admission cannot be
something a `rm -rf output/` destroys, or that a reader of the repository
cannot audit.

`output/<pipeline>/_afb_provenance.json` still overrides this file when
present, for local iteration. Anything that reaches a published leaderboard
should be declared here.

## Fields

| field | meaning |
| --- | --- |
| `model_version` | version string that identifies what actually answered |
| `mode` | named mode, when the harness config does not carry one |
| `seed_count` | seeds run (≥3 required if `sampled`) |
| `sampled` | true if the adapter samples; forces the 3-seed policy |
| `prompt_sha256` | frozen prompt hash, or `"none"` for prompt-free APIs |
| `reference_implementation` | true for the benchmark authors' own system |

Omit a field only when it is genuinely underivable and genuinely unknown — a
missing field rejects the row by name, which is the intended behaviour.
