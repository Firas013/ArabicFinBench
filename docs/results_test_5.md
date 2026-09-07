
# ArabicFinBench — test_5/Test_5  (canon 0.8.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.3559 | 0.4638 | **0.7243** | 0.8786 | 0.3684 | 9/9 | api |
| gemini-3.5-flash-lite | 0.2775 | 0.3434 | **0.6767** | 0.7110 | 0.3993 | 9/11 | api |
| qwen3.7-flash | 0.4495 | 0.5552 | **0.5593** | 0.7307 | 0.1097 | 9/10 | api |
| llamaparse_agentic_plus | 0.2585 | 0.3705 | **0.4894** | 0.6045 | 0.2309 | 9/9 | api |
| mistral_ocr_4 | 0.3600 | 0.4339 | **0.4365** | 0.6058 | 0.0765 | 9/10 | api |
| feras_model | 0.0865 | 0.1325 | **0.3233** | 0.5750 | 0.2369 | 9/9 | hand-imported |
| llamaparse_agentic | 0.3412 | 0.3951 | **0.2780** | 0.4845 | -0.0632 | 9/9 | api |
| gpt-5-mini | 0.0866 | 0.0890 | **0.2190** | 0.3405 | 0.1324 | 6/6 | api |
| mistral-medium-3.1 | 0.0654 | 0.1350 | **0.1904** | 0.4467 | 0.1250 | 9/17 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.9642 | 0.9085 | 0.0428 | 0.6439 | 0.2917 | 0.0358 | 132 |
| gemini-3.5-flash-lite | 0.9284 | 0.5423 | 0.4579 | 0.2153 | 0.7417 | 0.0716 | 144 |
| qwen3.7-flash | 0.9642 | 0.8803 | 0.0699 | 0.3561 | 0.6083 | 0.0358 | 132 |
| llamaparse_agentic_plus | 0.8239 | 0.6690 | 0.2867 | 0.3966 | 0.4083 | 0.1761 | 179 |
| mistral_ocr_4 | 0.8955 | 0.7676 | 0.2168 | 0.1935 | 0.7500 | 0.1045 | 155 |
| feras_model | 0.7791 | 0.6127 | 0.4351 | 0.5052 | 0.1833 | 0.2209 | 194 |
| llamaparse_agentic | 0.8388 | 0.2676 | 0.7047 | 0.3276 | 0.5250 | 0.1612 | 174 |
| gpt-5-mini | 0.4627 | 0.1549 | 0.8217 | 0.3333 | 0.1667 | 0.5373 | 300 |
| mistral-medium-3.1 | 0.7343 | 0.2535 | 0.6320 | 0.3732 | 0.3500 | 0.2657 | 209 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| qwen3.8-27b | 1.0000 | - | - | 2026-09-07T19:10:48 |
| gemini-3.5-flash-lite | 1.0000 | - | - | 2026-09-07T19:10:41 |
| qwen3.7-flash | 1.0000 | - | - | 2026-09-07T19:10:39 |
| llamaparse_agentic_plus | 0.9185 | 0.0563 | 53.2s | 2026-09-07T19:10:52 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T19:10:54 |
| feras_model | 1.0000 | 0.0000 | - | 2026-09-07T19:13:56 |
| llamaparse_agentic | 1.0000 | 0.0125 | 54.3s | 2026-09-07T19:10:50 |
| gpt-5-mini | 1.0000 | - | - | 2026-09-07T19:10:43 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T19:10:45 |

## F — arithmetic consistency

Does the system's *own* output add up? 19 identities are declared for this document — block sums and totals taken from the statement itself — and evaluated against each system's extracted figures under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it rather than being dropped: a system cannot earn arithmetic credit by declining to answer. `F (evaluable)` restricts to the relations it did supply figures for, which separates computing badly from extracting sparsely.

| system | F | F (evaluable) | reconciling | evaluable | declared |
| --- | --- | --- | --- | --- | --- |
| feras_model | **1.0000** | 1.0000 | 19 | 19 | 19 |
| gpt-5-mini | **1.0000** | 1.0000 | 19 | 19 | 19 |
| mistral_ocr_4 | **0.5789** | 0.8462 | 11 | 13 | 19 |
| llamaparse_agentic_plus | **0.3684** | 1.0000 | 7 | 7 | 19 |
| qwen3.7-flash | **0.3158** | 0.8571 | 6 | 7 | 19 |
| mistral-medium-3.1 | **0.3158** | 0.3158 | 6 | 19 | 19 |
| llamaparse_agentic | **0.2105** | 0.3636 | 4 | 11 | 19 |
| qwen3.8-27b | **0.1579** | 1.0000 | 3 | 3 | 19 |
| gemini-3.5-flash-lite | **0.1053** | 0.2000 | 2 | 10 | 19 |

*P, E and F are reported separately and never combined. A system that parses cleanly and computes wrongly is not partially correct — it produces confident, well-formed, wrong financial figures.*

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.7-flash, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
