
# ArabicFinBench — test_5/Test_5  (canon 0.7.0)

**What each column means: [docs/metrics.md](metrics.md).** In short — `struct` is the score, `raw` is what an unnormalised leaderboard would show, and the gap between them is convention rather than reading quality.

## P — table metrics, raw | text | struct

| system | TRM raw | TRM text | TRM struct | GriTS struct | raw→canon Δ | tables | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.3559 | 0.4638 | **0.7243** | 0.8786 | 0.3684 | 9/9 | api |
| gemini-3.5-flash-lite | 0.2775 | 0.3434 | **0.6767** | 0.7110 | 0.3993 | 9/11 | api |
| qwen3.7-flash | 0.4495 | 0.5552 | **0.4615** | 0.6864 | 0.0120 | 9/10 | api |
| mistral_ocr_4 | 0.3600 | 0.4339 | **0.4365** | 0.6058 | 0.0765 | 9/10 | api |
| llamaparse_agentic_plus | 0.2585 | 0.3705 | **0.4044** | 0.5763 | 0.1459 | 9/9 | api |
| feras_model | 0.0865 | 0.1325 | **0.3233** | 0.5750 | 0.2369 | 9/9 | hand-imported |
| llamaparse_agentic | 0.3412 | 0.3951 | **0.3175** | 0.4580 | -0.0237 | 9/9 | api |
| gpt-5-mini | 0.0866 | 0.0890 | **0.2190** | 0.3405 | 0.1324 | 6/6 | api |
| mistral-medium-3.1 | 0.0654 | 0.1350 | **0.1904** | 0.4467 | 0.1250 | 9/17 | api |

## P — cell metrics, and E — null correctness

| system | coverage | numeric exact | digit CER | null acc | fabricated | dropped | judged |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.9493 | 0.7254 | 0.2354 | 0.5912 | 0.3250 | 0.0507 | 137 |
| gemini-3.5-flash-lite | 0.8955 | 0.2746 | 0.6890 | 0.1290 | 0.8333 | 0.1045 | 155 |
| qwen3.7-flash | 0.9373 | 0.5141 | 0.4123 | 0.1277 | 0.8500 | 0.0627 | 141 |
| mistral_ocr_4 | 0.8090 | 0.5775 | 0.4151 | 0.1467 | 0.7750 | 0.1910 | 184 |
| llamaparse_agentic_plus | 0.9851 | 0.2746 | 0.6919 | 0.0400 | 0.9583 | 0.0149 | 125 |
| feras_model | 0.6299 | 0.0070 | 1.0399 | 0.3184 | 0.3500 | 0.3731 | 245 |
| llamaparse_agentic | 0.9791 | 0.0986 | 0.8716 | 0.0315 | 0.9667 | 0.0209 | 127 |
| gpt-5-mini | 0.4776 | 0.0845 | 0.9173 | 0.3186 | 0.2167 | 0.5224 | 295 |
| mistral-medium-3.1 | 0.6328 | 0.0704 | 0.8802 | 0.1646 | 0.6667 | 0.3672 | 243 |

## Diagnostics

| system | script fidelity | $/page | latency | scored at |
| --- | --- | --- | --- | --- |
| qwen3.8-27b | 1.0000 | - | - | 2026-09-07T17:11:41 |
| gemini-3.5-flash-lite | 1.0000 | - | - | 2026-09-07T17:11:34 |
| qwen3.7-flash | 1.0000 | - | - | 2026-09-07T17:11:31 |
| mistral_ocr_4 | 1.0000 | 0.0040 | 2.2s | 2026-09-07T17:11:47 |
| llamaparse_agentic_plus | 0.9185 | 0.0563 | 53.2s | 2026-09-07T17:11:45 |
| feras_model | 1.0000 | 0.0000 | - | 2026-09-07T17:14:47 |
| llamaparse_agentic | 1.0000 | 0.0125 | 54.3s | 2026-09-07T17:11:43 |
| gpt-5-mini | 1.0000 | - | - | 2026-09-07T17:11:35 |
| mistral-medium-3.1 | 1.0000 | - | - | 2026-09-07T17:11:38 |

**F (arithmetic): not reported — no MATH rules are authored for this document yet. The mechanism exists and is tested; the rules are a ground-truth authoring task.**

**No combined P/E/F score is emitted, by construction.** See `docs/fairness.md` guard 10.

*Served via OpenRouter rather than the vendor's own API: gemini-3.5-flash-lite, gpt-5-mini, mistral-medium-3.1, qwen3.7-flash, qwen3.8-27b. The store keeps these under distinct ids so the two routes are never conflated.*

## Did not produce output

| system | reason |
| --- | --- |
| qwen3.5-9b | Provider error: Empty content response from API |

*Scored zero on every dimension and listed here rather than dropped (guard 5). Ranked tables above exclude them: a zero from a failed call is not a measurement of reading quality.*
