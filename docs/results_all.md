# ArabicFinBench — full corpus matrix (canon 0.7.0)

Every system against every document, from the stored measurements in `results/scores.jsonl`. Column meanings: [docs/metrics.md](metrics.md).

**`fail`** = the run produced no output; the provider's error is in the
per-document tables. **`–`** = never run. Neither is a score of zero.


### P — table record match, `struct` pass

The score. Canon applied symmetrically to both sides.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.7648 | 0.6219 | n/a | 0.7623 | 0.6767 | 0.4802 | 0.6612 |
| qwen3.8-27b | 0.8711 | 0.4893 | n/a | 0.6235 | 0.7243 | 0.5399 | 0.6496 |
| llamaparse_agentic | 0.9799 | 0.4892 | n/a | 0.5533 | 0.3175 | 0.4765 | 0.5633 |
| llamaparse_agentic_plus | 0.5670 | 0.1759 | n/a | 0.6948 | 0.4044 | 0.3855 | 0.4455 |
| feras_model | 0.7895 | 0.4530 | n/a | 0.4002 | 0.3233 | 0.1977 | 0.4328 |
| mistral_ocr_4 | 0.4086 | 0.5045 | n/a | 0.3998 | 0.4365 | 0.4088 | 0.4316 |
| gpt-5-mini | 0.2528 | 0.1076 | n/a | 0.3734 | 0.2190 | 0.2390 | 0.2384 |
| mistral-medium-3.1 | 0.3464 | 0.2333 | n/a | 0.1402 | 0.1904 | 0.1540 | 0.2129 |
| qwen3.7-flash | **fail** | 0.5086 | n/a | **fail** | 0.4615 | **fail** | *2/5* |
| qwen3.5-9b | 0.7477 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |

### P — table record match, `raw` pass

What an unnormalised leaderboard would show. The gap to `struct` is convention — column direction and section rows — not reading quality.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8636 | 0.2662 | n/a | 0.1745 | 0.3559 | 0.2191 | 0.3759 |
| gemini-3.5-flash-lite | 0.8097 | 0.2864 | n/a | 0.1812 | 0.2775 | 0.1080 | 0.3325 |
| llamaparse_agentic_plus | 0.4732 | 0.0173 | n/a | 0.2936 | 0.2585 | 0.3078 | 0.2701 |
| mistral_ocr_4 | 0.5732 | 0.1335 | n/a | 0.1080 | 0.3600 | 0.1373 | 0.2624 |
| feras_model | 0.6319 | 0.2602 | n/a | 0.0613 | 0.0865 | 0.0232 | 0.2126 |
| llamaparse_agentic | 0.1511 | 0.0139 | n/a | 0.2977 | 0.3412 | 0.1373 | 0.1883 |
| gpt-5-mini | 0.4804 | 0.0253 | n/a | 0.0987 | 0.0866 | 0.1181 | 0.1618 |
| qwen3.5-9b | 0.7606 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |
| qwen3.7-flash | **fail** | 0.2033 | n/a | **fail** | 0.4495 | **fail** | *2/5* |
| mistral-medium-3.1 | 0.2359 | 0.1265 | n/a | 0.0194 | 0.0654 | 0.0413 | 0.0977 |

### P — GriTS content, `struct` pass

Content agreement over the paired table grids.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.9466 | 0.8501 | n/a | 0.7850 | 0.8786 | 0.7541 | 0.8429 |
| gemini-3.5-flash-lite | 0.8211 | 0.7508 | n/a | 0.8426 | 0.7110 | 0.6920 | 0.7635 |
| llamaparse_agentic | 0.9962 | 0.6740 | n/a | 0.6131 | 0.4580 | 0.6555 | 0.6793 |
| mistral_ocr_4 | 0.7580 | 0.7252 | n/a | 0.5804 | 0.6058 | 0.6259 | 0.6591 |
| feras_model | 0.8983 | 0.6772 | n/a | 0.6279 | 0.5750 | 0.4202 | 0.6397 |
| llamaparse_agentic_plus | 0.7438 | 0.5064 | n/a | 0.7173 | 0.5763 | 0.6236 | 0.6335 |
| mistral-medium-3.1 | 0.6420 | 0.5062 | n/a | 0.3999 | 0.4467 | 0.4973 | 0.4984 |
| gpt-5-mini | 0.5557 | 0.3403 | n/a | 0.6731 | 0.3405 | 0.5379 | 0.4895 |
| qwen3.7-flash | **fail** | 0.7171 | n/a | **fail** | 0.6864 | **fail** | *2/5* |
| qwen3.5-9b | 0.8801 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |

### Diagnostic — script fidelity

Fraction of the raw prediction's digit runs written in the script the page actually prints. Measured on raw output and never folded into a P score. `test_4` is the corpus's only Latin-digit filing, which is why this column separates there and nowhere else.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic_plus | 0.9972 | 0.9920 | n/a | 0.8855 | 0.9185 | 0.9669 | 0.9520 |
| gemini-3.5-flash-lite | 1.0000 | 0.9986 | n/a | 0.0247 | 1.0000 | 0.9957 | 0.8038 |
| mistral_ocr_4 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| mistral-medium-3.1 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| feras_model | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 0.9987 | 0.7997 |
| gpt-5-mini | 1.0000 | 0.9985 | n/a | 0.0000 | 1.0000 | 0.9880 | 0.7973 |
| qwen3.8-27b | 1.0000 | 0.7839 | n/a | 0.0035 | 1.0000 | 0.8804 | 0.7336 |
| llamaparse_agentic | 0.0000 | 1.0000 | n/a | 0.9278 | 1.0000 | 0.4930 | 0.6842 |
| qwen3.7-flash | **fail** | 1.0000 | n/a | **fail** | 1.0000 | **fail** | *2/5* |
| qwen3.5-9b | 1.0000 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |

## Documents not scored

- **test_3/Test_3** — no ground truth: `Test_3.json` is a byte-identical copy of `Test_4.json` (md5 `f022ef76…`) and describes `Test_4.pdf` (SABB). The Saudi Cement filing in `Test_3.pdf` has never been annotated.

## What this table does not say

- **The cell-level metrics are omitted deliberately.** `numeric_exact`, `digit_cer` and the null columns currently respond to column-order convention and a table-pairing failure on `test_6`, not to reading accuracy; mirroring a prediction's columns moved one system's `numeric_exact` from 0.0986 to 0.5000. They stay in the per-document files, and out of the corpus view, until that is fixed.
- **F (arithmetic) is absent** — no `math` rules are authored for any document yet.
- **No combined score is emitted**, by construction (guard 10).
- **Rankings are not significance-tested.** Five documents is not enough to separate systems a few hundredths apart.
