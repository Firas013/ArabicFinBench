# ArabicFinBench — full corpus matrix (canon 0.8.0)

Every system against every document, from the stored measurements in `results/scores.jsonl`. Column meanings: [docs/metrics.md](metrics.md).

**`fail`** = the run produced no output; the provider's error is in the
per-document tables. **`–`** = never run. Neither is a score of zero.


### P — table record match, `struct` pass

The score. Canon applied symmetrically to both sides.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-3.5-flash-lite | 0.7648 | 0.6219 | n/a | 0.7623 | 0.6767 | 0.4802 | 0.6612 |
| qwen3.8-27b | 0.8711 | 0.4893 | n/a | 0.6235 | 0.7243 | 0.5412 | 0.6499 |
| llamaparse_agentic | 0.9799 | 0.5047 | n/a | 0.5593 | 0.2780 | 0.4874 | 0.5619 |
| llamaparse_agentic_plus | 0.5670 | 0.2628 | n/a | 0.6968 | 0.4894 | 0.4257 | 0.4883 |
| paddleocr_ft_both | 0.7523 | 0.4724 | n/a | 0.4258 | 0.3542 | 0.2047 | 0.4419 |
| feras_model | 0.7895 | 0.4530 | n/a | 0.4002 | 0.3233 | 0.1977 | 0.4328 |
| feras_v10_320 | 0.7895 | 0.4530 | n/a | 0.4002 | 0.3233 | 0.1977 | 0.4328 |
| mistral_ocr_4 | 0.4086 | 0.5045 | n/a | 0.3998 | 0.4365 | 0.4096 | 0.4318 |
| feras_lay21_v10 | 0.7523 | 0.4473 | n/a | 0.4083 | 0.3369 | 0.2047 | 0.4299 |
| feras_v13new_320 | 0.7458 | 0.3840 | n/a | 0.3531 | 0.3028 | 0.1999 | 0.3971 |
| feras_v13_320 | 0.6051 | 0.3770 | n/a | 0.3212 | 0.2909 | 0.1894 | 0.3567 |
| paddleocr_ft_rec | 0.4759 | 0.2798 | n/a | 0.3418 | 0.1310 | 0.1434 | 0.2744 |
| gpt-5-mini | 0.2528 | 0.1076 | n/a | 0.3734 | 0.2190 | 0.2387 | 0.2383 |
| qwen3.7-flash | **fail** | 0.5086 | n/a | **fail** | 0.5593 | **fail** | *2/5* |
| mistral-medium-3.1 | 0.3464 | 0.2333 | n/a | 0.1402 | 0.1904 | 0.1537 | 0.2128 |
| paddleocr_ft_layout | 0.2574 | 0.2127 | n/a | 0.2247 | 0.2284 | 0.1125 | 0.2072 |
| qwen3.5-9b | 0.7477 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |
| paddleocr_stock | 0.2054 | 0.1140 | n/a | 0.1891 | 0.1084 | 0.0800 | 0.1394 |

### P — table record match, `raw` pass

What an unnormalised leaderboard would show. The gap to `struct` is convention — column direction and section rows — not reading quality.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.8636 | 0.2662 | n/a | 0.1745 | 0.3559 | 0.2191 | 0.3759 |
| gemini-3.5-flash-lite | 0.8097 | 0.2864 | n/a | 0.1812 | 0.2775 | 0.1080 | 0.3325 |
| llamaparse_agentic_plus | 0.4732 | 0.0173 | n/a | 0.2936 | 0.2585 | 0.3078 | 0.2701 |
| mistral_ocr_4 | 0.5732 | 0.1335 | n/a | 0.1080 | 0.3600 | 0.1373 | 0.2624 |
| feras_v13_320 | 0.6763 | 0.2453 | n/a | 0.0615 | 0.0788 | 0.0224 | 0.2169 |
| feras_model | 0.6319 | 0.2602 | n/a | 0.0613 | 0.0865 | 0.0232 | 0.2126 |
| feras_v10_320 | 0.6319 | 0.2602 | n/a | 0.0613 | 0.0865 | 0.0232 | 0.2126 |
| paddleocr_ft_both | 0.6169 | 0.2541 | n/a | 0.0548 | 0.1080 | 0.0173 | 0.2102 |
| feras_lay21_v10 | 0.6169 | 0.2476 | n/a | 0.0559 | 0.0924 | 0.0173 | 0.2060 |
| feras_v13new_320 | 0.6025 | 0.2363 | n/a | 0.0667 | 0.0802 | 0.0207 | 0.2013 |
| llamaparse_agentic | 0.1511 | 0.0139 | n/a | 0.2977 | 0.3412 | 0.1373 | 0.1883 |
| gpt-5-mini | 0.4804 | 0.0253 | n/a | 0.0987 | 0.0866 | 0.1181 | 0.1618 |
| qwen3.5-9b | 0.7606 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |
| qwen3.7-flash | **fail** | 0.2033 | n/a | **fail** | 0.4495 | **fail** | *2/5* |
| mistral-medium-3.1 | 0.2359 | 0.1265 | n/a | 0.0194 | 0.0654 | 0.0413 | 0.0977 |
| paddleocr_ft_layout | 0.1460 | 0.1382 | n/a | 0.0572 | 0.1152 | 0.0171 | 0.0947 |
| paddleocr_ft_rec | 0.1365 | 0.1645 | n/a | 0.0538 | 0.0709 | 0.0109 | 0.0873 |
| paddleocr_stock | 0.0962 | 0.0756 | n/a | 0.0553 | 0.0751 | 0.0093 | 0.0623 |

### P — GriTS content, `struct` pass

Content agreement over the paired table grids.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3.8-27b | 0.9466 | 0.8501 | n/a | 0.7850 | 0.8786 | 0.7545 | 0.8430 |
| gemini-3.5-flash-lite | 0.8211 | 0.7508 | n/a | 0.8426 | 0.7110 | 0.6924 | 0.7636 |
| llamaparse_agentic | 0.9962 | 0.6841 | n/a | 0.6302 | 0.4845 | 0.6378 | 0.6866 |
| mistral_ocr_4 | 0.7580 | 0.7252 | n/a | 0.5804 | 0.6058 | 0.6263 | 0.6591 |
| llamaparse_agentic_plus | 0.7438 | 0.5849 | n/a | 0.7322 | 0.6045 | 0.6243 | 0.6579 |
| paddleocr_ft_both | 0.8689 | 0.6904 | n/a | 0.6175 | 0.6201 | 0.4310 | 0.6456 |
| feras_lay21_v10 | 0.8689 | 0.6767 | n/a | 0.6226 | 0.6050 | 0.4310 | 0.6408 |
| feras_model | 0.8983 | 0.6772 | n/a | 0.6279 | 0.5750 | 0.4206 | 0.6398 |
| feras_v10_320 | 0.8983 | 0.6772 | n/a | 0.6279 | 0.5750 | 0.4206 | 0.6398 |
| feras_v13new_320 | 0.8887 | 0.6619 | n/a | 0.6235 | 0.5664 | 0.4138 | 0.6309 |
| feras_v13_320 | 0.8412 | 0.6573 | n/a | 0.6138 | 0.5619 | 0.4274 | 0.6203 |
| paddleocr_ft_layout | 0.6960 | 0.6046 | n/a | 0.5654 | 0.5646 | 0.3784 | 0.5618 |
| mistral-medium-3.1 | 0.6420 | 0.5062 | n/a | 0.3999 | 0.4467 | 0.4974 | 0.4984 |
| gpt-5-mini | 0.5557 | 0.3403 | n/a | 0.6731 | 0.3405 | 0.5380 | 0.4895 |
| paddleocr_ft_rec | 0.5041 | 0.4795 | n/a | 0.5329 | 0.2363 | 0.3151 | 0.4136 |
| paddleocr_stock | 0.4312 | 0.4048 | n/a | 0.4770 | 0.2160 | 0.2761 | 0.3610 |
| qwen3.7-flash | **fail** | 0.7171 | n/a | **fail** | 0.7307 | **fail** | *2/5* |
| qwen3.5-9b | 0.8801 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |

### F — arithmetic consistency

Share of the statement's own declared identities that the system's extracted figures satisfy, under exact `Fraction` arithmetic. A relation whose figures the system never produced counts against it: arithmetic credit cannot be earned by declining to answer. **Never combined with P or E** — a system that parses cleanly and computes wrongly is not partially correct.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| feras_model | 1.0000 | 0.6250 | n/a | 1.0000 | 1.0000 | 0.8889 | 0.9028 |
| feras_v10_320 | 1.0000 | 0.6250 | n/a | 1.0000 | 1.0000 | 0.8889 | 0.9028 |
| paddleocr_ft_both | 1.0000 | 0.5000 | n/a | 1.0000 | 1.0000 | 0.9259 | 0.8852 |
| feras_lay21_v10 | 1.0000 | 0.5000 | n/a | 1.0000 | 0.8947 | 0.9259 | 0.8641 |
| llamaparse_agentic | 1.0000 | 1.0000 | n/a | 1.0000 | 0.2105 | 0.7407 | 0.7903 |
| paddleocr_ft_rec | 1.0000 | 0.6250 | n/a | 1.0000 | 0.2632 | 0.8889 | 0.7554 |
| mistral_ocr_4 | 1.0000 | 0.9375 | n/a | 0.0000 | 0.5789 | 0.7037 | 0.6440 |
| llamaparse_agentic_plus | 0.8750 | 0.0625 | n/a | 1.0000 | 0.3684 | 0.8148 | 0.6241 |
| feras_v13new_320 | 1.0000 | 0.0000 | n/a | 0.0000 | 1.0000 | 0.7407 | 0.5481 |
| feras_v13_320 | 1.0000 | 0.0000 | n/a | 0.0000 | 1.0000 | 0.7037 | 0.5407 |
| gemini-3.5-flash-lite | 0.8125 | 0.7500 | n/a | 0.0000 | 0.1053 | 0.5556 | 0.4447 |
| gpt-5-mini | 0.3125 | 0.7500 | n/a | 0.0000 | 1.0000 | 0.0370 | 0.4199 |
| qwen3.8-27b | 0.5625 | 0.4375 | n/a | 0.0000 | 0.1579 | 0.2593 | 0.2834 |
| mistral-medium-3.1 | 0.0625 | 0.6875 | n/a | 0.0000 | 0.3158 | 0.1111 | 0.2354 |
| qwen3.7-flash | **fail** | 0.6875 | n/a | **fail** | 0.3158 | **fail** | *2/5* |
| qwen3.5-9b | 0.8750 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |
| paddleocr_stock | 0.0000 | 0.0000 | n/a | 0.0000 | 0.1053 | 0.0000 | 0.0211 |
| paddleocr_ft_layout | 0.0000 | 0.0000 | n/a | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Diagnostic — script fidelity

Fraction of the raw prediction's digit runs written in the script the page actually prints. Measured on raw output and never folded into a P score. `test_4` is the corpus's only Latin-digit filing, which is why this column separates there and nowhere else.

| system | test_1 | test_2 | test_3 | test_4 | test_5 | test_6 | mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llamaparse_agentic_plus | 0.9972 | 0.9920 | n/a | 0.8855 | 0.9185 | 0.9669 | 0.9520 |
| gemini-3.5-flash-lite | 1.0000 | 0.9986 | n/a | 0.0247 | 1.0000 | 0.9957 | 0.8038 |
| feras_v13new_320 | 1.0000 | 1.0000 | n/a | 0.0007 | 1.0000 | 0.9993 | 0.8000 |
| feras_lay21_v10 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| mistral_ocr_4 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| mistral-medium-3.1 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| paddleocr_ft_both | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 1.0000 | 0.8000 |
| paddleocr_stock | 1.0000 | 1.0000 | n/a | 0.0007 | 1.0000 | 0.9992 | 0.8000 |
| paddleocr_ft_rec | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 0.9994 | 0.7999 |
| feras_v13_320 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 0.9987 | 0.7997 |
| feras_model | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 0.9987 | 0.7997 |
| feras_v10_320 | 1.0000 | 1.0000 | n/a | 0.0000 | 1.0000 | 0.9987 | 0.7997 |
| paddleocr_ft_layout | 1.0000 | 1.0000 | n/a | 0.0007 | 1.0000 | 0.9960 | 0.7993 |
| gpt-5-mini | 1.0000 | 0.9985 | n/a | 0.0000 | 1.0000 | 0.9880 | 0.7973 |
| qwen3.8-27b | 1.0000 | 0.7839 | n/a | 0.0035 | 1.0000 | 0.8804 | 0.7336 |
| llamaparse_agentic | 0.0000 | 1.0000 | n/a | 0.9278 | 1.0000 | 0.4930 | 0.6842 |
| qwen3.7-flash | **fail** | 1.0000 | n/a | **fail** | 1.0000 | **fail** | *2/5* |
| qwen3.5-9b | 1.0000 | **fail** | n/a | **fail** | **fail** | **fail** | *1/5* |

## Documents not scored

- **test_3/Test_3** — no ground truth: `Test_3.json` is a byte-identical copy of `Test_4.json` (md5 `f022ef76…`) and describes `Test_4.pdf`. The filing in `Test_3.pdf` has never been annotated.

## What this table does not say

- **The cell-level metrics are omitted deliberately.** `numeric_exact`, `digit_cer` and the null columns currently respond to column-order convention and a table-pairing failure on `test_6`, not to reading accuracy; mirroring a prediction's columns moved one system's `numeric_exact` from 0.0986 to 0.5000. They stay in the per-document files, and out of the corpus view, until that is fixed.
- **F (arithmetic) is absent** — no `math` rules are authored for any document yet.
- **No combined score is emitted**, by construction (guard 10).
- **Rankings are not significance-tested.** Five documents is not enough to separate systems a few hundredths apart.
