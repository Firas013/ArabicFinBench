#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score @Feras_model (GVP local chain) on any document under the CURRENT canon,
capture the full metric set, append to results/scores.jsonl as a hand-imported dev
row, and print it (with any same-document competitor rows). Offline, deterministic.
Usage: uv run python score_doc.py <gt.json> <pred_v3.txt> <document-id>"""
import json, html, sys

def esc(s): return html.escape(str(s or ""))

def gt_markup(path):
    d = json.load(open(path))
    parts = [esc(l["text"]) for l in d.get("lines", [])]
    for t in d.get("tables", []):
        h = "<table>"
        for r in t["rows"]:
            h += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
        parts.append(h + "</table>")
    return "\n\n".join(parts)

def pred_markup(path):
    d = open(path, encoding="utf-8").read()
    pages = json.loads(d.split("PAGES=", 1)[1].split("\nSTATS=", 1)[0])
    parts = []
    for pg in pages:
        regs = {}
        for l in pg["lines"]:
            regs.setdefault(l.get("rid"), []).append(l)
        for rid, ls in sorted(regs.items(), key=lambda kv: min(x["y"] for x in kv[1])):
            cols = {l.get("col", 0) for l in ls}
            if len(cols) > 1:
                rows, maxc = {}, max(cols)
                for l in ls:
                    rows.setdefault(l.get("row", 0), {})[l.get("col", 0)] = l["t"]
                h = "<table>"
                for ri in sorted(rows):
                    h += "<tr>" + "".join(f"<td>{esc(rows[ri].get(c,''))}</td>" for c in range(maxc+1)) + "</tr>"
                parts.append(h + "</table>")
            else:
                for l in sorted(ls, key=lambda z: (round(z["y"],3), -z["x"])):
                    parts.append(esc(l["t"]))
    return "\n\n".join(parts)

gtp, predp, docid = sys.argv[1], sys.argv[2], sys.argv[3]
from arabicfinbench.scoring import score_document, CANON_VERSION
from arabicfinbench import results

GT, PRED = gt_markup(gtp), pred_markup(predp)
print(f"canon={CANON_VERSION}  doc={docid}  GT {GT.count('<table>')} tables/{len(GT)} chars  |  "
      f"PRED {PRED.count('<table>')} tables/{len(PRED)} chars")

score = score_document(GT, PRED, source=f"feras_model/{docid}")
row = results.from_document_score(score, system="feras_model", document=docid,
                                  cost_per_page_usd=0.0, median_latency_ms=None, status="hand-imported")
results.append([row])
print(f"appended feras_model row (canon {row.canon_version})")

rows = [r for r in results.latest(document=docid, canon_version=CANON_VERSION)
        if r.status != "failed" and r.passes.get("struct", {}).get("grits_trm_composite") is not None]
def g(r,p,m): return r.passes.get(p,{}).get(m)
rows.sort(key=lambda r:(g(r,"struct","grits_trm_composite") or 0), reverse=True)
def f(v,n=3): return "  -  " if v is None else f"{v:.{n}f}"
print(f"\n=== {docid}, canon {CANON_VERSION} (sorted by struct grits_trm) ===")
print(f"{'system':22s} | {'raw_trm':>7s} {'txt_trm':>7s} {'str_trm':>7s} | {'str_con':>7s} | "
      f"{'num_ex':>6s} {'dgtCER':>6s} {'cover':>6s} | {'nul_ac':>6s} {'fab':>6s} {'drop':>6s} | {'scrpt':>5s}")
for r in rows:
    mark = " <==" if r.system == "feras_model" else ""
    print(f"{r.system:22s} | {f(g(r,'raw','grits_trm_composite')):>7s} {f(g(r,'text','grits_trm_composite')):>7s} "
          f"{f(g(r,'struct','grits_trm_composite')):>7s} | {f(g(r,'struct','grits_con')):>7s} | "
          f"{f(r.numeric_exact):>6s} {f(r.digit_cer):>6s} {f(r.coverage):>6s} | "
          f"{f(r.null_accuracy):>6s} {f(r.null_fabricated):>6s} {f(r.null_dropped):>6s} | {f(r.script_fidelity,2):>5s}{mark}")
