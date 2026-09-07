
# ArabicFinBench — test_4/Test_4  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.1812 | 0.5464 | **0.7623** | 0.8426 | 0.5811 | 18/23 | api |
| llamaparse_agentic_plus | 0.2936 | 0.3985 | **0.6948** | 0.7173 | 0.4012 | 18/19 | api |
| qwen3.8-27b | 0.1745 | 0.4688 | **0.6235** | 0.7850 | 0.4489 | 18/18 | api |
| llamaparse_agentic | 0.2977 | 0.3416 | **0.5533** | 0.6131 | 0.2555 | 18/18 | api |
| feras_model | 0.0613 | 0.1091 | **0.4002** | 0.6279 | 0.3389 | 18/18 | hand-imported |
| mistral_ocr_4 | 0.1080 | 0.3718 | **0.3998** | 0.5804 | 0.2918 | 17/17 | api |
| gpt-5-mini | 0.0987 | 0.3235 | **0.3734** | 0.6731 | 0.2747 | 18/18 | api |
| mistral-medium-3.1 | 0.0194 | 0.0288 | **0.1402** | 0.3999 | 0.1209 | 18/18 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9235 | 0.4728 | 0.4280 | 0.5892 | 0.2510 | 0.0869 | 314 |
| llamaparse_agentic_plus | 0.9300 | 0.3771 | 0.5526 | 0.3538 | 0.4858 | 0.1453 | 359 |
| qwen3.8-27b | 0.9585 | 0.2345 | 0.5389 | 0.6677 | 0.1538 | 0.0856 | 313 |
| llamaparse_agentic | 0.8936 | 0.0919 | 0.8314 | 0.3307 | 0.4980 | 0.1660 | 375 |
| feras_model | 0.7328 | 0.0356 | 0.9758 | 0.2848 | 0.4777 | 0.2672 | 453 |
| mistral_ocr_4 | 0.8379 | 0.2101 | 0.6145 | 0.4458 | 0.2834 | 0.1946 | 397 |
| gpt-5-mini | 0.7873 | 0.1182 | 0.7247 | 0.4161 | 0.3077 | 0.2127 | 411 |
| mistral-medium-3.1 | 0.6719 | 0.0356 | 0.8559 | 0.2836 | 0.3684 | 0.3930 | 550 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.0247 | - | - | 2026-09-07T17:09:42 |
| llamaparse_agentic_plus | 0.8855 | 0.0563 | 53.2s | 2026-09-07T17:11:09 |
| qwen3.8-27b | 0.0035 | - | - | 2026-09-07T17:10:32 |
| llamaparse_agentic | 0.9278 | 0.0125 | 54.3s | 2026-09-07T17:10:50 |
| feras_model | 0.0000 | 0.0000 | - | 2026-09-07T17:14:42 |
| mistral_ocr_4 | 0.0000 | 0.0040 | 2.2s | 2026-09-07T17:11:26 |
| gpt-5-mini | 0.0000 | - | - | 2026-09-07T17:09:58 |
| mistral-medium-3.1 | 0.0000 | - | - | 2026-09-07T17:10:14 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
