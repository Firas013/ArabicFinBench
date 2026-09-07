
# ArabicFinBench — test_2/Test_2  (canon 0.8.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.2864 | 0.3009 | **0.6219** | 0.7508 | 0.3355 | 9/9 | api |
| qwen3.7-flash | 0.2033 | 0.2033 | **0.5086** | 0.7171 | 0.3053 | 9/13 | api |
| llamaparse_agentic | 0.0139 | 0.0139 | **0.5047** | 0.6841 | 0.4908 | 9/9 | api |
| mistral_ocr_4 | 0.1335 | 0.1335 | **0.5045** | 0.7252 | 0.3710 | 9/9 | api |
| qwen3.8-27b | 0.2662 | 0.3069 | **0.4893** | 0.8501 | 0.2231 | 9/9 | api |
| feras_model | 0.2602 | 0.2602 | **0.4530** | 0.6772 | 0.1929 | 9/9 | hand-imported |
| llamaparse_agentic_plus | 0.0173 | 0.0173 | **0.2628** | 0.5849 | 0.2455 | 9/10 | api |
| mistral-medium-3.1 | 0.1265 | 0.1327 | **0.2333** | 0.5062 | 0.1068 | 9/14 | api |
| gpt-5-mini | 0.0253 | 0.0253 | **0.1076** | 0.3403 | 0.0823 | 7/7 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9272 | 0.6854 | 0.2247 | 0.5631 | 0.2368 | 0.0756 | 103 |
| qwen3.7-flash | 0.9104 | 0.5728 | 0.2686 | 0.5804 | 0.1447 | 0.1008 | 112 |
| llamaparse_agentic | 0.9496 | 0.4554 | 0.4714 | 0.5312 | 0.3289 | 0.0560 | 96 |
| mistral_ocr_4 | 0.9300 | 0.7887 | 0.1629 | 0.5534 | 0.2500 | 0.0756 | 103 |
| qwen3.8-27b | 0.9860 | 0.4507 | 0.0947 | 0.9259 | 0.0132 | 0.0140 | 81 |
| feras_model | 0.8487 | 0.6854 | 0.3200 | 0.5769 | 0.0132 | 0.1513 | 130 |
| llamaparse_agentic_plus | 0.8739 | 0.4789 | 0.3813 | 0.4390 | 0.2895 | 0.1317 | 123 |
| mistral-medium-3.1 | 0.6779 | 0.3052 | 0.4610 | 0.2784 | 0.2895 | 0.3305 | 194 |
| gpt-5-mini | 0.5742 | 0.0751 | 0.7360 | 0.2632 | 0.2105 | 0.4258 | 228 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9986 | - | - | 2026-09-07T19:08:16 |
| qwen3.7-flash | 1.0000 | - | - | 2026-09-07T19:08:14 |
| llamaparse_agentic | 1.0000 | 0.0125 | 54.3s | 2026-09-07T19:08:25 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T19:08:29 |
| qwen3.8-27b | 0.7839 | - | - | 2026-09-07T19:08:23 |
| feras_model | 1.0000 | 0.0000 | - | 2026-09-07T19:13:30 |
| llamaparse_agentic_plus | 0.9920 | 0.0563 | 53.2s | 2026-09-07T19:08:28 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T19:08:20 |
| gpt-5-mini | 0.9985 | - | - | 2026-09-07T19:08:18 |

## F — arithmetic consistency

Does the system's *own* output add up? 16 identities are declared for this document — block sums and totals taken from the statement itself — and evaluated against each system's extracted figures under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it rather than being dropped: a system cannot earn arithmetic credit by declining to answer. `F (evaluable)` restricts to the relations it did supply figures for, which separates computing badly from extracting sparsely.

| system | F | F (evaluable) | reconciling | evaluable | declared |
| --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | **1.0000** | 1.0000 | 16 | 16 | 16 |
| mistral_ocr_4 | **0.9375** | 1.0000 | 15 | 15 | 16 |
| gemini-3.5-flash-lite | **0.7500** | 0.8000 | 12 | 15 | 16 |
| gpt-5-mini | **0.7500** | 0.7500 | 12 | 16 | 16 |
| qwen3.7-flash | **0.6875** | 0.6875 | 11 | 16 | 16 |
| mistral-medium-3.1 | **0.6875** | 0.6875 | 11 | 16 | 16 |
| feras_model | **0.6250** | 0.7692 | 10 | 13 | 16 |
| qwen3.8-27b | **0.4375** | 0.4375 | 7 | 16 | 16 |
| llamaparse_agentic_plus | **0.0625** | 0.2500 | 1 | 4 | 16 |

*P, E and F are reported separately and never combined. A system that parses cleanly and computes wrongly is not partially correct — it produces confident, well-formed, wrong financial figures.*

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.7-flash, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
