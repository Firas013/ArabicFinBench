
# ArabicFinBench — test_1/Test_1  (canon 0.4.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.3195 | 0.8149 | **0.9129** | 0.9194 | 0.5934 | 5/5 | api |
| llamaparse_agentic_plus | 0.6875 | 0.6875 | **0.7821** | 0.8894 | 0.0946 | 5/5 | api |
| datalab_web | 0.7445 | 0.7519 | **0.7766** | 0.8716 | 0.0322 | 5/6 | hand-imported |
| datalab_accurate | 0.7413 | 0.7488 | **0.7728** | 0.8628 | 0.0314 | 5/6 | api |
| mistral_ocr_4 | 0.4509 | 0.4541 | **0.4685** | 0.6532 | 0.0176 | 5/10 | api |
| llamaparse_provided | 0.4105 | 0.4105 | **0.4483** | 0.8734 | 0.0378 | 5/6 | hand-imported |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.9954 | 0.8197 | 0.1951 | 0.6579 | 0.1935 | 0.0347 | 38 |
| llamaparse_agentic_plus | 0.9633 | 0.7049 | 0.2877 | 0.5556 | 0.1935 | 0.0693 | 45 |
| datalab_web | 0.8670 | 0.7295 | 0.2975 | 0.3871 | 0.2258 | 0.1535 | 62 |
| datalab_accurate | 0.8670 | 0.7295 | 0.2975 | 0.3871 | 0.2258 | 0.1535 | 62 |
| mistral_ocr_4 | 0.7339 | 0.7213 | 0.2901 | 0.3494 | 0.0645 | 0.2574 | 83 |
| llamaparse_provided | 0.6330 | 0.1148 | 0.8704 | 0.1619 | 0.4516 | 0.3663 | 105 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.2402 | 0.0125 | 37.9s | 2026-09-02T10:45:47 |
| llamaparse_agentic_plus | 0.9947 | 0.0563 | 49.5s | 2026-09-02T10:45:48 |
| datalab_web | 1.0000 | - | - | 2026-09-02T10:45:50 |
| datalab_accurate | 1.0000 | 0.0100 | 32.9s | 2026-09-02T10:45:50 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.7s | 2026-09-02T10:45:51 |
| llamaparse_provided | 0.9489 | - | - | 2026-09-02T10:45:49 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.
