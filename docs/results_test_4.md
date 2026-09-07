
# ArabicFinBench — test_4/Test_4  (canon 0.8.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.1812 | 0.5464 | **0.7623** | 0.8426 | 0.5811 | 18/23 | api |
| llamaparse_agentic_plus | 0.2936 | 0.3985 | **0.6968** | 0.7322 | 0.4033 | 18/19 | api |
| qwen3.8-27b | 0.1745 | 0.4688 | **0.6235** | 0.7850 | 0.4489 | 18/18 | api |
| llamaparse_agentic | 0.2977 | 0.3416 | **0.5593** | 0.6302 | 0.2615 | 18/18 | api |
| feras_model | 0.0613 | 0.1091 | **0.4002** | 0.6279 | 0.3389 | 18/18 | hand-imported |
| mistral_ocr_4 | 0.1080 | 0.3718 | **0.3998** | 0.5804 | 0.2918 | 17/17 | api |
| gpt-5-mini | 0.0987 | 0.3235 | **0.3734** | 0.6731 | 0.2747 | 18/18 | api |
| mistral-medium-3.1 | 0.0194 | 0.0288 | **0.1402** | 0.3999 | 0.1209 | 18/18 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9546 | 0.6679 | 0.1763 | 0.6643 | 0.2308 | 0.0506 | 286 |
| llamaparse_agentic_plus | 0.9157 | 0.5872 | 0.3586 | 0.6939 | 0.0729 | 0.1077 | 330 |
| qwen3.8-27b | 0.9741 | 0.4128 | 0.2337 | 0.8625 | 0.0607 | 0.0285 | 269 |
| llamaparse_agentic | 0.9196 | 0.5047 | 0.4235 | 0.5455 | 0.2713 | 0.1077 | 330 |
| feras_model | 0.9248 | 0.8199 | 0.1952 | 0.7377 | 0.0891 | 0.0752 | 305 |
| mistral_ocr_4 | 0.8923 | 0.4916 | 0.2582 | 0.6181 | 0.1417 | 0.1245 | 343 |
| gpt-5-mini | 0.8586 | 0.2795 | 0.4423 | 0.5562 | 0.1984 | 0.1414 | 356 |
| mistral-medium-3.1 | 0.7523 | 0.1013 | 0.6692 | 0.3793 | 0.2874 | 0.2815 | 464 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.0247 | - | - | 2026-09-07T19:08:49 |
| llamaparse_agentic_plus | 0.8855 | 0.0563 | 53.2s | 2026-09-07T19:10:17 |
| qwen3.8-27b | 0.0035 | - | - | 2026-09-07T19:09:39 |
| llamaparse_agentic | 0.9278 | 0.0125 | 54.3s | 2026-09-07T19:09:58 |
| feras_model | 0.0000 | 0.0000 | - | 2026-09-07T19:13:51 |
| mistral_ocr_4 | 0.0000 | 0.0040 | 2.2s | 2026-09-07T19:10:34 |
| gpt-5-mini | 0.0000 | - | - | 2026-09-07T19:09:05 |
| mistral-medium-3.1 | 0.0000 | - | - | 2026-09-07T19:09:21 |

## F — arithmetic consistency

Does the system's *own* output add up? 3 identities are declared for this document — block sums and totals taken from the statement itself — and evaluated against each system's extracted figures under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it rather than being dropped: a system cannot earn arithmetic credit by declining to answer. `F (evaluable)` restricts to the relations it did supply figures for, which separates computing badly from extracting sparsely.

| system | F | F (evaluable) | reconciling | evaluable | declared |
| --- | --- | --- | --- | --- | --- |
| llamaparse_agentic_plus | **1.0000** | 1.0000 | 3 | 3 | 3 |
| llamaparse_agentic | **1.0000** | 1.0000 | 3 | 3 | 3 |
| feras_model | **1.0000** | 1.0000 | 3 | 3 | 3 |
| gemini-3.5-flash-lite | **0.0000** | 0.0000 | 0 | 3 | 3 |
| qwen3.8-27b | **0.0000** | 0.0000 | 0 | 3 | 3 |
| mistral_ocr_4 | **0.0000** | 0.0000 | 0 | 3 | 3 |
| gpt-5-mini | **0.0000** | 0.0000 | 0 | 3 | 3 |
| mistral-medium-3.1 | **0.0000** | 0.0000 | 0 | 2 | 3 |

*P, E and F are reported separately and never combined. A system that parses cleanly and computes wrongly is not partially correct — it produces confident, well-formed, wrong financial figures.*

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
