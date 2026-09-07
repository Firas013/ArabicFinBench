
# ArabicFinBench — test_6/Test_6  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.2191 | 0.4158 | **0.5412** | 0.7545 | 0.3222 | 19/21 | api |
| gemini-3.5-flash-lite | 0.1080 | 0.2478 | **0.4802** | 0.6924 | 0.3722 | 19/30 | api |
| llamaparse_agentic | 0.1373 | 0.4032 | **0.4778** | 0.6558 | 0.3405 | 19/21 | api |
| mistral_ocr_4 | 0.1373 | 0.3843 | **0.4096** | 0.6263 | 0.2723 | 19/20 | api |
| llamaparse_agentic_plus | 0.3078 | 0.5549 | **0.3873** | 0.6240 | 0.0795 | 19/23 | api |
| gpt-5-mini | 0.1181 | 0.1762 | **0.2387** | 0.5380 | 0.1207 | 19/21 | api |
| feras_model | 0.0232 | 0.0247 | **0.1977** | 0.4206 | 0.1745 | 19/21 | hand-imported |
| mistral-medium-3.1 | 0.0413 | 0.0473 | **0.1537** | 0.4974 | 0.1124 | 19/23 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8644 | 0.3212 | 0.5450 | 0.3758 | 0.3778 | 0.1345 | 298 |
| gemini-3.5-flash-lite | 0.8655 | 0.2974 | 0.6718 | 0.3211 | 0.4667 | 0.1357 | 299 |
| llamaparse_agentic | 0.9028 | 0.1369 | 0.7874 | 0.3872 | 0.4278 | 0.0981 | 266 |
| mistral_ocr_4 | 0.8136 | 0.1898 | 0.7714 | 0.2174 | 0.5833 | 0.1881 | 345 |
| llamaparse_agentic_plus | 0.8701 | 0.1898 | 0.7622 | 0.2847 | 0.5333 | 0.1311 | 295 |
| gpt-5-mini | 0.6633 | 0.1807 | 0.7479 | 0.2102 | 0.4500 | 0.3318 | 471 |
| feras_model | 0.5582 | 0.0109 | 0.9379 | 0.1489 | 0.5278 | 0.4458 | 571 |
| mistral-medium-3.1 | 0.6960 | 0.0201 | 0.9207 | 0.1814 | 0.5222 | 0.3352 | 474 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8804 | - | - | 2026-09-07T17:46:42 |
| gemini-3.5-flash-lite | 0.9957 | - | - | 2026-09-07T17:45:39 |
| llamaparse_agentic | 0.4930 | 0.0125 | 54.3s | 2026-09-07T17:47:02 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T17:47:42 |
| llamaparse_agentic_plus | 0.9669 | 0.0563 | 53.2s | 2026-09-07T17:47:24 |
| gpt-5-mini | 0.9880 | - | - | 2026-09-07T17:45:58 |
| feras_model | 0.9987 | 0.0000 | - | 2026-09-07T17:48:36 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T17:46:19 |

## F — arithmetic consistency

Does the system's *own* output add up? 27 identities are declared for this document — block sums and totals taken from the statement itself — and evaluated against each system's extracted figures under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it rather than being dropped: a system cannot earn arithmetic credit by declining to answer. `F (evaluable)` restricts to the relations it did supply figures for, which separates computing badly from extracting sparsely.

| system | F | F (evaluable) | reconciling | evaluable | declared |
| --- | --- | --- | --- | --- | --- |
| gpt-5-mini | **0.2593** | 0.3889 | 7 | 18 | 27 |
| feras_model | **0.1481** | 0.1600 | 4 | 25 | 27 |
| gemini-3.5-flash-lite | **0.0741** | 0.1053 | 2 | 19 | 27 |
| qwen3.8-27b | **0.0000** | 0.0000 | 0 | 20 | 27 |
| llamaparse_agentic | **0.0000** | 0.0000 | 0 | 21 | 27 |
| mistral_ocr_4 | **0.0000** | 0.0000 | 0 | 16 | 27 |
| llamaparse_agentic_plus | **0.0000** | 0.0000 | 0 | 20 | 27 |
| mistral-medium-3.1 | **0.0000** | 0.0000 | 0 | 6 | 27 |

*P, E and F are reported separately and never combined. A system that parses cleanly and computes wrongly is not partially correct — it produces confident, well-formed, wrong financial figures.*

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
