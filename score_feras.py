#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score @Feras_model (GVP) on Test_1 with the REAL harness scorer.
GT: test1/Test_1.json (lines + 5 tables, spatial order). Prediction: our chain's
/tmp/test_1_v3.txt units, reassembled into HTML tables by (region,row,col).
Both sides -> markup; score_document applies canon symmetrically (digit script +
column direction), three passes raw|text|struct, plus script fidelity."""
import json, re, html

def esc(s): return html.escape(str(s or ""))

def gt_markup(path):
    d = json.load(open(path))
    parts = [esc(l["text"]) for l in d.get("lines", [])]
    for t in d.get("tables", []):
        rows = t["rows"]
        h = "<table>"
        for r in rows:
            h += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
        parts.append(h + "</table>")
    return "\n\n".join(parts)

def pred_markup(path):
    d = open(path, encoding="utf-8").read()
    pages = json.loads(d.split("PAGES=", 1)[1].split("\nSTATS=", 1)[0])
    parts = []
    for pg in pages:
        # group units by region id
        regs = {}
        for l in pg["lines"]:
            regs.setdefault(l.get("rid"), []).append(l)
        # region order by min-y
        for rid, ls in sorted(regs.items(), key=lambda kv: min(x["y"] for x in kv[1])):
            cols = {l.get("col", 0) for l in ls}
            if len(cols) > 1:                      # table region -> HTML table
                rows = {}
                maxc = max(cols)
                for l in ls:
                    rows.setdefault(l.get("row", 0), {})[l.get("col", 0)] = l["t"]
                h = "<table>"
                for ri in sorted(rows):
                    h += "<tr>" + "".join(f"<td>{esc(rows[ri].get(c,''))}</td>" for c in range(maxc+1)) + "</tr>"
                parts.append(h + "</table>")
            else:                                   # prose -> text, reading order
                for l in sorted(ls, key=lambda z: (round(z["y"],3), -z["x"])):
                    parts.append(esc(l["t"]))
    return "\n\n".join(parts)

from arabicfinbench.scoring import score_document
GT = gt_markup("test1/Test_1.json")
PRED = pred_markup("/tmp/test_1_v3.txt")
print(f"GT markup {len(GT)} chars, {GT.count('<table>')} tables;  "
      f"PRED {len(PRED)} chars, {PRED.count('<table>')} tables")
r = score_document(GT, PRED, source="feras_model/test_1/Test_1")
print("\n=== @Feras_model (GVP) — real ArabicFinBench scorer, Test_1 ===")
for tier in ("raw", "text", "struct"):
    p = r.passes[tier]
    print(f"  {tier:6s}  GriTS-con={p.get('grits_con',0):.3f}  "
          f"struct-TRM={p.get('grits_trm_composite',0):.3f}  "
          f"struct-consistency={p.get('structural_consistency',0):.3f}  "
          f"tables paired={p.get('tables_paired',0):.0f}/{p.get('tables_expected',0):.0f}")
print(f"  script_fidelity = {r.script_fidelity}")
print(f"  gt rules fired: {r.gt_trace}  |  pred rules fired: {r.pred_trace}")
