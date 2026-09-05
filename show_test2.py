#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only: print the test_2/Test_2 dev-report table from results/scores.jsonl
at the current canon, sorted by struct grits_trm. Does not modify the store."""
from arabicfinbench.scoring import CANON_VERSION
from arabicfinbench import results

rows = [r for r in results.latest(document="test_2/Test_2", canon_version=CANON_VERSION)
        if r.status != "failed" and r.passes.get("struct", {}).get("grits_trm_composite") is not None]
def g(r,p,m): return r.passes.get(p,{}).get(m)
rows.sort(key=lambda r:(g(r,"struct","grits_trm_composite") or 0), reverse=True)
def f(v,n=3): return "  -  " if v is None else f"{v:.{n}f}"
print(f"=== test_2/Test_2 · canon {CANON_VERSION} · {len(rows)} systems (sorted by struct grits_trm) ===")
print(f"{'system':24s} | {'raw_trm':>7s} {'txt_trm':>7s} {'str_trm':>7s} | {'str_con':>7s} | "
      f"{'num_ex':>6s} {'dgtCER':>6s} {'cover':>6s} | {'nul_ac':>6s} {'fab':>6s} {'drop':>6s} | {'scrpt':>5s}")
for r in rows:
    mark = " <== @Feras" if r.system == "feras_model" else ""
    print(f"{r.system:24s} | {f(g(r,'raw','grits_trm_composite')):>7s} {f(g(r,'text','grits_trm_composite')):>7s} "
          f"{f(g(r,'struct','grits_trm_composite')):>7s} | {f(g(r,'struct','grits_con')):>7s} | "
          f"{f(r.numeric_exact):>6s} {f(r.digit_cer):>6s} {f(r.coverage):>6s} | "
          f"{f(r.null_accuracy):>6s} {f(r.null_fabricated):>6s} {f(r.null_dropped):>6s} | {f(r.script_fidelity,2):>5s}{mark}")
