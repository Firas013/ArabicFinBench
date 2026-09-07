
# ArabicFinBench — test_1/Test_1  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.1511 | 0.7133 | **0.9799** | 0.9962 | 0.8288 | 5/5 | api |
| qwen3.8-27b | 0.8636 | 0.8673 | **0.8711** | 0.9466 | 0.0075 | 5/5 | api |
| feras_model | 0.6319 | 0.6319 | **0.7895** | 0.8983 | 0.1577 | 5/5 | hand-imported |
| gemini-3.5-flash-lite | 0.8097 | 0.8158 | **0.7648** | 0.8211 | -0.0449 | 5/5 | api |
| qwen3.5-9b | 0.7606 | 0.7621 | **0.7477** | 0.8801 | -0.0129 | 5/6 | api |
| llamaparse_agentic_plus | 0.4732 | 0.4732 | **0.5670** | 0.7438 | 0.0938 | 5/5 | api |
| mistral_ocr_4 | 0.5732 | 0.5763 | **0.4086** | 0.7580 | -0.1646 | 5/8 | api |
| mistral-medium-3.1 | 0.2359 | 0.2359 | **0.3464** | 0.6420 | 0.1105 | 5/7 | api |
| gpt-5-mini | 0.4804 | 0.4804 | **0.2528** | 0.5557 | -0.2276 | 5/5 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.9954 | 1.0000 | 0.0000 | 0.9688 | 0.0000 | 0.0050 | 32 |
| qwen3.8-27b | 0.9541 | 0.8934 | 0.0210 | 1.0000 | 0.0000 | 0.0000 | 31 |
| feras_model | 0.8991 | 0.9262 | 0.0778 | 0.6190 | 0.1613 | 0.0545 | 42 |
| gemini-3.5-flash-lite | 0.8991 | 0.7295 | 0.2778 | 0.3878 | 0.3871 | 0.0891 | 49 |
| qwen3.5-9b | 0.9174 | 0.7869 | 0.2198 | 0.5200 | 0.1613 | 0.0941 | 50 |
| llamaparse_agentic_plus | 0.8716 | 0.1803 | 0.7630 | 0.2879 | 0.3871 | 0.1733 | 66 |
| mistral_ocr_4 | 0.8303 | 0.7295 | 0.2605 | 0.3944 | 0.0968 | 0.1980 | 71 |
| mistral-medium-3.1 | 0.7706 | 0.3115 | 0.4235 | 0.2603 | 0.3871 | 0.2079 | 73 |
| gpt-5-mini | 0.5872 | 0.2541 | 0.7481 | 0.1441 | 0.4839 | 0.3960 | 111 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| llamaparse_agentic | 0.0000 | 0.0125 | 54.3s | 2026-09-07T17:42:30 |
| qwen3.8-27b | 1.0000 | - | - | 2026-09-07T17:42:29 |
| feras_model | 1.0000 | 0.0000 | - | 2026-09-07T17:47:44 |
| gemini-3.5-flash-lite | 1.0000 | - | - | 2026-09-07T17:42:27 |
| qwen3.5-9b | 1.0000 | - | - | 2026-09-07T17:42:29 |
| llamaparse_agentic_plus | 0.9972 | 0.0563 | 53.2s | 2026-09-07T17:42:31 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T17:42:31 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T17:42:28 |
| gpt-5-mini | 1.0000 | - | - | 2026-09-07T17:42:27 |

## F — arithmetic consistency

Does the system's *own* output add up? 16 identities are declared for this document — block sums and totals taken from the statement itself — and evaluated against each system's extracted figures under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it rather than being dropped: a system cannot earn arithmetic credit by declining to answer. `F (evaluable)` restricts to the relations it did supply figures for, which separates computing badly from extracting sparsely.

| system | F | F (evaluable) | reconciling | evaluable | declared |
| --- | --- | --- | --- | --- | --- |
| llamaparse_agentic | **1.0000** | 1.0000 | 16 | 16 | 16 |
| feras_model | **1.0000** | 1.0000 | 16 | 16 | 16 |
| mistral_ocr_4 | **1.0000** | 1.0000 | 16 | 16 | 16 |
| qwen3.5-9b | **0.8750** | 0.8750 | 14 | 16 | 16 |
| gemini-3.5-flash-lite | **0.8125** | 0.8667 | 13 | 15 | 16 |
| qwen3.8-27b | **0.5625** | 0.6923 | 9 | 13 | 16 |
| mistral-medium-3.1 | **0.0625** | 0.0769 | 1 | 13 | 16 |
| gpt-5-mini | **0.0625** | 0.1429 | 1 | 7 | 16 |
| llamaparse_agentic_plus | **0.0000** | 0.0000 | 0 | 12 | 16 |

*P, E and F are reported separately and never combined. A system that parses cleanly and computes wrongly is not partially correct — it produces confident, well-formed, wrong financial figures.*

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.5-9b, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.7-flash | Provider error: HTTP 429: {"error":{"message":"Provider returned error","code":429,"metadata":{"raw":"qwen/qwen3.7-flash is temporarily rate-limited upstream. P |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
