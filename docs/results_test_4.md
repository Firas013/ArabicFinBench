
# ArabicFinBench — test_4/Test_4  (canon 0.6.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.1812 | 0.5464 | **0.6778** | 0.8173 | 0.4966 | 18/23 | api |
| llamaparse_agentic_plus | 0.2936 | 0.3985 | **0.6514** | 0.7061 | 0.3578 | 18/19 | api |
| qwen3.8-27b | 0.1745 | 0.4688 | **0.6235** | 0.7850 | 0.4489 | 18/18 | api |
| llamaparse_agentic | 0.2977 | 0.3416 | **0.5533** | 0.6131 | 0.2555 | 18/18 | api |
| feras_model | 0.0613 | 0.1091 | **0.4002** | 0.6279 | 0.3389 | 18/18 | hand-imported |
| mistral_ocr_4 | 0.1080 | 0.3718 | **0.3998** | 0.5804 | 0.2918 | 17/17 | api |
| gpt-5-mini | 0.0987 | 0.3235 | **0.3734** | 0.6731 | 0.2747 | 18/18 | api |
| mistral-medium-3.1 | 0.0194 | 0.0288 | **0.1431** | 0.4256 | 0.1237 | 18/18 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9507 | 0.3827 | 0.5170 | 0.6769 | 0.1943 | 0.0610 | 294 |
| llamaparse_agentic_plus | 0.9287 | 0.3621 | 0.5604 | 0.3846 | 0.4534 | 0.1349 | 351 |
| qwen3.8-27b | 0.9585 | 0.2345 | 0.5389 | 0.6677 | 0.1538 | 0.0856 | 313 |
| llamaparse_agentic | 0.8936 | 0.0919 | 0.8314 | 0.3307 | 0.4980 | 0.1660 | 375 |
| feras_model | 0.7328 | 0.0356 | 0.9758 | 0.2848 | 0.4777 | 0.2672 | 453 |
| mistral_ocr_4 | 0.8379 | 0.2101 | 0.6145 | 0.4458 | 0.2834 | 0.1946 | 397 |
| gpt-5-mini | 0.7873 | 0.1182 | 0.7247 | 0.4161 | 0.3077 | 0.2127 | 411 |
| mistral-medium-3.1 | 0.6732 | 0.0450 | 0.8506 | 0.2907 | 0.3563 | 0.3891 | 547 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.0247 | - | - | 2026-09-07T16:09:51 |
| llamaparse_agentic_plus | 0.8855 | 0.0563 | 53.2s | 2026-09-07T16:11:18 |
| qwen3.8-27b | 0.0035 | - | - | 2026-09-07T16:10:41 |
| llamaparse_agentic | 0.9278 | 0.0125 | 54.3s | 2026-09-07T16:10:59 |
| feras_model | 0.0000 | 0.0000 | - | 2026-09-07T16:11:57 |
| mistral_ocr_4 | 0.0000 | 0.0040 | 2.2s | 2026-09-07T16:11:36 |
| gpt-5-mini | 0.0000 | - | - | 2026-09-07T16:10:07 |
| mistral-medium-3.1 | 0.0000 | - | - | 2026-09-07T16:10:23 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
