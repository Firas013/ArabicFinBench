cd /home/feras/ArabicFinBench
.venv/bin/python - <<'PY' 2>&1 | grep -viE "^  grits|table pair"
import json, re
from pathlib import Path
from arabicfinbench.scoring import score_document
gt = Path("test_1/Test_1.md").read_text(encoding="utf-8")
def fold(doc):
    return re.sub(r"<(/?)th\b", r"<\1td", doc)
for name in ("or_gemini_3_5_flash_lite","or_qwen3_7_flash","llamaparse_agentic"):
    md = json.loads(Path(f"output/{name}/test_1/Test_1.result.json").read_text(encoding="utf-8"))["output"]["markdown"]
    b = score_document(gt, md, source=name).passes["struct"]
    a = score_document(fold(gt), fold(md), source=name).passes["struct"]
    print(f"RESULT {name:<26} TRM {b['table_record_match']:.4f} -> {a['table_record_match']:.4f}   GriTS {b['grits_con']:.4f} -> {a['grits_con']:.4f}")
PY
