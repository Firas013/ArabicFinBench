# scripts/

Command-line entry points. Grouped here by what they are for; the directory is
flat because the paths appear in documentation and commit messages, and renaming
them would break every recorded command for no gain.

## Authoring and checking ground truth

| script | what it does |
| --- | --- |
| `afb_gt_to_sidecar.py` | ground truth → `expected_markdown` + harness sidecar. Run after any edit to a `.json`. |
| `afb_gt_correct.py` | the only supported way to change an authored cell. Refuses unless `--expect` matches, and cannot write a correction without its log entry. |
| `afb_consensus.py` | flags cells where independent systems agree against the ground truth — the likeliest annotator error. |
| `afb_freeze.py` | sha256 commitment over the test split. |

## Running systems

| script | what it does |
| --- | --- |
| `afb_run_openrouter.py` | runs the OpenRouter VLMs through the harness, with the frozen prompt and its hash. |
| `afb_score_feras_model.py` | scores the local GVP chain against the same sidecar every API row is scored against. |
| `afb_import_*.py` | import a hand-run console export. Stamped `hand-imported`; the leaderboard withholds those by default because their tier, cost and latency cannot be verified. |

## Reporting

| script | what it does |
| --- | --- |
| `afb_results.py` | `--record` scores into the store; without it, renders one document's table from what is already stored. The two are separate on purpose: a reported table must not depend on what the code was doing when someone asked to see it. |
| `afb_matrix.py` | the corpus view — every system against every document, one metric per table. |
| `afb_leaderboard.py` | row assembly and admission; names its refusals rather than dropping rows. |
| `afb_score_parse.py` | the three canon passes side by side, plus per-table diagnostics. |

## Repository plumbing

| script | what it does |
| --- | --- |
| `install-hooks.sh` | points `core.hooksPath` at the tracked `hooks/`, so hook changes reach everyone on their next pull. |
| `hooks/pre-commit` | refuses to commit a corpus document. CI enforces the same rule, so skipping the hook does not get one merged. |

Nothing else lives here. Three upstream or incidental scripts were removed
rather than left to be mistaken for part of the benchmark: `update_readme.py`
(regenerated leaderboard tables from a root `leaderboard.csv` this fork does not
have, and errored), `bench_table_metrics.py` (an upstream one-off comparing
table-metric implementations), and `clean_zone_identifiers.py` (a Windows/WSL
housekeeping utility). `afb_matrix.py` and `afb_results.py` render every table
this benchmark publishes.
