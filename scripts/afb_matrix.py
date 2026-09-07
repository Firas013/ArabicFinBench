#!/usr/bin/env python3
"""Render every system against every document, one metric per table.

``afb_results.py`` renders one document. This renders the corpus: the same
stored, stamped numbers arranged system x document, which is the view that shows
whether a lead survives more than one filing.

Reads only ``results/scores.jsonl`` -- no scoring, no API calls -- so the matrix
cannot disagree with the per-document tables.

Two rules it keeps:

* **Metrics are never mixed.** Each table is one metric across all documents.
  P, E and F are not combined here any more than they are anywhere else
  (``docs/fairness.md`` guard 10).
* **A mean is printed only for a system scored on every document.** With
  unequal coverage an average silently rewards whoever failed on the hard
  pages, so partial rows show their count instead.

Usage::

    python scripts/afb_matrix.py
    python scripts/afb_matrix.py --out docs/results_all.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from arabicfinbench.canon.version import CANON_VERSION
from arabicfinbench.results import STORE

# Every document the corpus contains, in order -- including ones nothing can be
# scored on. A document missing from the table is indistinguishable from one
# nobody ran; a document present and empty states its own reason.
CORPUS: tuple[tuple[str, str], ...] = (
    ("test_1/Test_1", "test_1"),
    ("test_2/Test_2", "test_2"),
    ("test_3/Test_3", "test_3"),
    ("test_4/Test_4", "test_4"),
    ("test_5/Test_5", "test_5"),
    ("test_6/Test_6", "test_6"),
)

UNSCOREABLE = {
    "test_3/Test_3": (
        "no ground truth: `Test_3.json` is a byte-identical copy of `Test_4.json` "
        "(md5 `f022ef76…`) and describes `Test_4.pdf` (SABB). The Saudi Cement "
        "filing in `Test_3.pdf` has never been annotated."
    ),
}


def load(canon: str) -> dict[tuple[str, str], dict]:
    """Latest row per (system, document) at one canon version."""
    rows: dict[tuple[str, str], dict] = {}
    for line in Path(STORE).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["canon_version"] == canon:
            rows[(r["system"], r["document"])] = r  # append-only: later wins
    return rows


def _display(system: str) -> str:
    from arabicfinbench.pipelines import OPENROUTER_VLMS

    model = OPENROUTER_VLMS.get(system)
    return model.split("/", 1)[-1] if model else system


def _value(row: dict | None, metric: str, pass_: str | None) -> float | None:
    if row is None or row["status"] == "failed":
        return None
    return row["passes"].get(pass_, {}).get(metric) if pass_ else row.get(metric)


def table(rows, systems, metric, pass_, title, note) -> list[str]:
    docs = [d for d, _ in CORPUS if d not in UNSCOREABLE]
    out = [f"\n### {title}\n", note, ""]
    out.append("| system | " + " | ".join(l for d, l in CORPUS) + " | mean |")
    out.append("|" + " --- |" * (len(CORPUS) + 2))
    ranked = sorted(
        systems,
        key=lambda s: -sum(_value(rows.get((s, d)), metric, pass_) or 0 for d in docs),
    )
    for s in ranked:
        cells, got = [], []
        for d, _ in CORPUS:
            if d in UNSCOREABLE:
                cells.append("n/a")
                continue
            row = rows.get((s, d))
            if row is None:
                cells.append("–")
            elif row["status"] == "failed":
                cells.append("**fail**")
            else:
                v = _value(row, metric, pass_)
                cells.append("–" if v is None else f"{v:.4f}")
                if v is not None:
                    got.append(v)
        mean = f"{sum(got) / len(got):.4f}" if len(got) == len(docs) else f"*{len(got)}/{len(docs)}*"
        out.append(f"| {_display(s)} | " + " | ".join(cells) + f" | {mean} |")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canon", default=CANON_VERSION)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rows = load(args.canon)
    if not rows:
        print(f"no rows at canon {args.canon} in {STORE}")
        return 1
    systems = sorted({s for s, _ in rows})

    out = [f"# ArabicFinBench — full corpus matrix (canon {args.canon})\n"]
    out.append(
        "Every system against every document, from the stored measurements in "
        "`results/scores.jsonl`. Column meanings: [docs/metrics.md](metrics.md).\n"
    )
    out.append("**`fail`** = the run produced no output; the provider's error is in the")
    out.append("per-document tables. **`–`** = never run. Neither is a score of zero.\n")

    out += table(
        rows, systems, "table_record_match", "struct",
        "P — table record match, `struct` pass",
        "The score. Canon applied symmetrically to both sides.",
    )
    out += table(
        rows, systems, "table_record_match", "raw",
        "P — table record match, `raw` pass",
        "What an unnormalised leaderboard would show. The gap to `struct` is "
        "convention — column direction and section rows — not reading quality.",
    )
    out += table(
        rows, systems, "grits_con", "struct",
        "P — GriTS content, `struct` pass",
        "Content agreement over the paired table grids.",
    )
    out += table(
        rows, systems, "arithmetic_consistency", None,
        "F — arithmetic consistency",
        "Share of the statement's own declared identities that the system's "
        "extracted figures satisfy, under exact `Fraction` arithmetic. A relation "
        "whose figures the system never produced counts against it: arithmetic "
        "credit cannot be earned by declining to answer. **Never combined with P "
        "or E** — a system that parses cleanly and computes wrongly is not "
        "partially correct.",
    )
    out += table(
        rows, systems, "script_fidelity", None,
        "Diagnostic — script fidelity",
        "Fraction of the raw prediction's digit runs written in the script the "
        "page actually prints. Measured on raw output and never folded into a P "
        "score. `test_4` is the corpus's only Latin-digit filing, which is why "
        "this column separates there and nowhere else.",
    )

    out.append("\n## Documents not scored\n")
    for doc, reason in UNSCOREABLE.items():
        out.append(f"- **{doc}** — {reason}")

    out.append(
        "\n## What this table does not say\n\n"
        "- **The cell-level metrics are omitted deliberately.** `numeric_exact`, "
        "`digit_cer` and the null columns currently respond to column-order "
        "convention and a table-pairing failure on `test_6`, not to reading "
        "accuracy; mirroring a prediction's columns moved one system's "
        "`numeric_exact` from 0.0986 to 0.5000. They stay in the per-document "
        "files, and out of the corpus view, until that is fixed.\n"
        "- **F (arithmetic) is absent** — no `math` rules are authored for any "
        "document yet.\n"
        "- **No combined score is emitted**, by construction (guard 10).\n"
        "- **Rankings are not significance-tested.** Five documents is not enough "
        "to separate systems a few hundredths apart."
    )

    text = "\n".join(out) + "\n"
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
