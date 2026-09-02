
# ArabicFinBench — test_1/Test_1  (canon 0.5.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.5843 | 0.5905 | **0.9421** | 0.9172 | 0.3578 | 5/5 | api |
| qwen3.8-27b | 0.8222 | 0.8222 | **0.8765** | 0.9859 | 0.0542 | 5/5 | api |
| qwen3.7-flash | 0.9052 | 0.9126 | **0.8738** | 0.9554 | -0.0314 | 5/6 | api |
| llamaparse_agentic | 0.3195 | 0.8149 | **0.8466** | 0.9194 | 0.5271 | 5/5 | api |
| llamaparse_agentic_plus | 0.6875 | 0.6875 | **0.8429** | 0.8894 | 0.1554 | 5/5 | api |
| qwen3.5-9b | 0.5009 | 0.5025 | **0.8147** | 0.9414 | 0.3138 | 5/5 | api |
| datalab_accurate | 0.7413 | 0.7488 | **0.7123** | 0.8628 | -0.0290 | 5/6 | api |
| mistral_ocr_4 | 0.4509 | 0.4541 | **0.3718** | 0.6532 | -0.0792 | 5/10 | api |
| mistral-medium-3.1 | 0.2104 | 0.2104 | **0.2864** | 0.6270 | 0.0760 | 5/7 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9495 | 0.9836 | 0.0173 | 0.8824 | 0.0323 | 0.0149 | 34 |
| qwen3.8-27b | 0.9954 | 0.9180 | 0.0160 | 0.9677 | 0.0323 | 0.0000 | 31 |
| qwen3.7-flash | 0.8165 | 0.6885 | 0.2716 | 0.4328 | 0.0645 | 0.1782 | 67 |
| llamaparse_agentic | 0.9954 | 0.8197 | 0.1951 | 0.6579 | 0.1935 | 0.0347 | 38 |
| llamaparse_agentic_plus | 0.9633 | 0.7049 | 0.2877 | 0.5556 | 0.1935 | 0.0693 | 45 |
| qwen3.5-9b | 0.9633 | 0.8770 | 0.0963 | 0.6429 | 0.1290 | 0.0545 | 42 |
| datalab_accurate | 0.8670 | 0.7295 | 0.2975 | 0.3871 | 0.2258 | 0.1535 | 62 |
| mistral_ocr_4 | 0.7339 | 0.7213 | 0.2901 | 0.3494 | 0.0645 | 0.2574 | 83 |
| mistral-medium-3.1 | 0.5688 | 0.0000 | 0.9852 | 0.1140 | 0.5806 | 0.4109 | 114 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 1.0000 | - | - | 2026-09-02T13:33:10 |
| qwen3.8-27b | 1.0000 | - | - | 2026-09-02T13:41:39 |
| qwen3.7-flash | 1.0000 | - | - | 2026-09-02T13:33:10 |
| llamaparse_agentic | 0.2402 | 0.0125 | 37.9s | 2026-09-02T13:33:07 |
| llamaparse_agentic_plus | 0.9947 | 0.0563 | 49.5s | 2026-09-02T13:33:07 |
| qwen3.5-9b | 1.0000 | - | - | 2026-09-02T14:35:44 |
| datalab_accurate | 1.0000 | 0.0100 | 32.9s | 2026-09-02T13:33:08 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.7s | 2026-09-02T13:33:09 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-02T13:33:11 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, mistral-medium-3.1, qwen3.5-9b, qwen3.7-flash, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| gpt-5-mini | no inference result produced |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*

*Not shown: datalab_web, llamaparse_provided — console exports whose tier, cost and latency cannot be verified. Still recorded in `results/scores.jsonl`; `--include-hand-imported` shows them.*
