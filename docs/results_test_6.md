
# ArabicFinBench — test_6/Test_6  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.2191 | 0.4156 | **0.5399** | 0.7541 | 0.3209 | 19/21 | api |
| gemini-3.5-flash-lite | 0.1080 | 0.2478 | **0.4802** | 0.6920 | 0.3722 | 19/30 | api |
| llamaparse_agentic | 0.1373 | 0.4032 | **0.4765** | 0.6555 | 0.3391 | 19/21 | api |
| mistral_ocr_4 | 0.1373 | 0.3840 | **0.4088** | 0.6259 | 0.2715 | 19/20 | api |
| llamaparse_agentic_plus | 0.3078 | 0.5534 | **0.3855** | 0.6236 | 0.0776 | 19/23 | api |
| gpt-5-mini | 0.1181 | 0.1762 | **0.2390** | 0.5379 | 0.1209 | 19/21 | api |
| feras_model | 0.0232 | 0.0247 | **0.1977** | 0.4202 | 0.1745 | 19/21 | hand-imported |
| mistral-medium-3.1 | 0.0413 | 0.0473 | **0.1540** | 0.4973 | 0.1126 | 19/23 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8643 | 0.3218 | 0.5443 | 0.3746 | 0.3812 | 0.1347 | 299 |
| gemini-3.5-flash-lite | 0.8654 | 0.2980 | 0.6714 | 0.3200 | 0.4696 | 0.1358 | 300 |
| llamaparse_agentic | 0.9027 | 0.1371 | 0.7872 | 0.3858 | 0.4309 | 0.0982 | 267 |
| mistral_ocr_4 | 0.8133 | 0.1901 | 0.7709 | 0.2168 | 0.5856 | 0.1884 | 346 |
| llamaparse_agentic_plus | 0.8699 | 0.1901 | 0.7620 | 0.2838 | 0.5359 | 0.1313 | 296 |
| gpt-5-mini | 0.6640 | 0.1810 | 0.7474 | 0.2123 | 0.4475 | 0.3311 | 471 |
| feras_model | 0.5577 | 0.0110 | 0.9378 | 0.1486 | 0.5304 | 0.4463 | 572 |
| mistral-medium-3.1 | 0.6957 | 0.0201 | 0.9203 | 0.1811 | 0.5249 | 0.3356 | 475 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8804 | - | - | 2026-09-07T17:13:13 |
| gemini-3.5-flash-lite | 0.9957 | - | - | 2026-09-07T17:12:11 |
| llamaparse_agentic | 0.4930 | 0.0125 | 54.3s | 2026-09-07T17:13:34 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T17:14:13 |
| llamaparse_agentic_plus | 0.9669 | 0.0563 | 53.2s | 2026-09-07T17:13:55 |
| gpt-5-mini | 0.9880 | - | - | 2026-09-07T17:12:31 |
| feras_model | 0.9987 | 0.0000 | - | 2026-09-07T17:15:07 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T17:12:51 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
