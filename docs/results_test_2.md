
# ArabicFinBench — test_2/Test_2  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.2864 | 0.3009 | **0.6219** | 0.7508 | 0.3355 | 9/9 | api |
| qwen3.7-flash | 0.2033 | 0.2033 | **0.5086** | 0.7171 | 0.3053 | 9/13 | api |
| mistral_ocr_4 | 0.1335 | 0.1335 | **0.5045** | 0.7252 | 0.3710 | 9/9 | api |
| qwen3.8-27b | 0.2662 | 0.3069 | **0.4893** | 0.8501 | 0.2231 | 9/9 | api |
| llamaparse_agentic | 0.0139 | 0.0139 | **0.4892** | 0.6740 | 0.4753 | 9/9 | api |
| feras_model | 0.2602 | 0.2602 | **0.4530** | 0.6772 | 0.1929 | 9/9 | hand-imported |
| mistral-medium-3.1 | 0.1265 | 0.1327 | **0.2333** | 0.5062 | 0.1068 | 9/14 | api |
| llamaparse_agentic_plus | 0.0173 | 0.0173 | **0.1759** | 0.5064 | 0.1586 | 9/10 | api |
| gpt-5-mini | 0.0253 | 0.0253 | **0.1076** | 0.3403 | 0.0823 | 7/7 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.8880 | 0.4507 | 0.4604 | 0.4016 | 0.3553 | 0.1289 | 122 |
| qwen3.7-flash | 0.8768 | 0.1080 | 0.7770 | 0.3984 | 0.3289 | 0.1457 | 128 |
| mistral_ocr_4 | 0.8739 | 0.3709 | 0.5350 | 0.3721 | 0.3684 | 0.1485 | 129 |
| qwen3.8-27b | 0.9244 | 0.2066 | 0.5927 | 0.5922 | 0.1974 | 0.0756 | 103 |
| llamaparse_agentic | 0.9496 | 0.0939 | 0.7868 | 0.2679 | 0.6053 | 0.1008 | 112 |
| feras_model | 0.6695 | 0.1643 | 0.8544 | 0.3026 | 0.2237 | 0.3333 | 195 |
| mistral-medium-3.1 | 0.5686 | 0.0704 | 0.8631 | 0.1810 | 0.4474 | 0.4370 | 232 |
| llamaparse_agentic_plus | 0.8852 | 0.0000 | 0.9359 | 0.0942 | 0.8289 | 0.1737 | 138 |
| gpt-5-mini | 0.5294 | 0.0094 | 0.9110 | 0.1803 | 0.4211 | 0.4706 | 244 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.9986 | - | - | 2026-09-07T17:09:09 |
| qwen3.7-flash | 1.0000 | - | - | 2026-09-07T17:09:07 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T17:09:22 |
| qwen3.8-27b | 0.7839 | - | - | 2026-09-07T17:09:16 |
| llamaparse_agentic | 1.0000 | 0.0125 | 54.3s | 2026-09-07T17:09:18 |
| feras_model | 1.0000 | 0.0000 | - | 2026-09-07T17:14:21 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T17:09:14 |
| llamaparse_agentic_plus | 0.9920 | 0.0563 | 53.2s | 2026-09-07T17:09:21 |
| gpt-5-mini | 0.9985 | - | - | 2026-09-07T17:09:11 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.7-flash, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
