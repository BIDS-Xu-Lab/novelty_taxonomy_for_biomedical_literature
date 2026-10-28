"""Novelty-claim counts and top-level shares for every (subfield, decade) cell.

Feeds historical_dynamics.py, which keeps cells with at least 100 mapped novelty claims.

Output: outputs/fig3/fill_shares.tsv — BST × decade claim count (N_labeled) and C/F/M shares
"""
from pathlib import Path
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nobl import paths
from nobl.taxonomy import get_leaf_to_top, read_hierarchy

OUT_DIR = paths.OUTPUT_DIR / "fig3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_SHARES = OUT_DIR / "fill_shares.tsv"

# Decade buckets: 1980s .. 2010s + 2020-2024. Anything before 1980 goes to "pre-1980".
DECADE_EDGES = [
    ("pre-1980", (None, 1979)),
    ("1980s",    (1980, 1989)),
    ("1990s",    (1990, 1999)),
    ("2000s",    (2000, 2009)),
    ("2010s",    (2010, 2019)),
    ("2020-2024", (2020, 2024)),
]
DECADE_ORDER = [name for name, _ in DECADE_EDGES]
TOPS = ("Concept Novelty", "Finding Novelty", "Method And/Or Material Novelty")


def year_to_decade(y):
    if y is None or (isinstance(y, float) and np.isnan(y)):
        return None
    y = int(y)
    for name, (lo, hi) in DECADE_EDGES:
        if (lo is None or lo <= y) and y <= hi:
            return name
    return None  # post-2024, if any


def main():
    df = pd.read_parquet(paths.LABELS_WITH_YEAR, columns=["pmid", "output", "year"])
    df["pmid"] = df["pmid"].astype(str)
    df["output"] = df["output"].str.lower().str.strip()

    # top-level category of each novelty claim; 'not novelty' and off-taxonomy outputs are dropped
    df["top"] = df["output"].map(get_leaf_to_top(read_hierarchy(paths.TAXONOMY)))
    df["decade"] = df["year"].apply(year_to_decade)
    lab = df.dropna(subset=["top", "decade"])
    print(f"* {len(lab):,} mapped novelty claims with a decade")

    pmid_labels = defaultdict(list)
    for pmid, top, decade in zip(lab["pmid"].values, lab["top"].values, lab["decade"].values):
        pmid_labels[pmid].append((top, decade))

    # an article in several subfields counts towards each of them
    subfields = pd.read_csv(paths.ARTICLE_SUBFIELDS, sep="\t", dtype={"pmid": str})
    rows = []
    for bst, pmids in sorted(subfields.groupby("bst")["pmid"]):
        cell = defaultdict(Counter)  # cell[decade][top] = n
        for pm in pmids:
            for top, dec in pmid_labels.get(pm, ()):
                cell[dec][top] += 1
        for dec in DECADE_ORDER:
            c = cell.get(dec, Counter())
            rows.append({"bst": bst, "decade": dec, "N_labeled": sum(c.values()), **{t: c.get(t, 0) for t in TOPS}})
    out = pd.DataFrame(rows)

    for t in TOPS:
        out[t.replace(" Novelty", "") + " %"] = np.where(out["N_labeled"] > 0, out[t] / out["N_labeled"] * 100, np.nan)
    out = out[["bst", "decade", "N_labeled", "Concept %", "Finding %", "Method And/Or Material %", *TOPS]]
    out.to_csv(OUT_SHARES, sep="\t", index=False)
    print(f"wrote {OUT_SHARES} ({out['bst'].nunique()} subfields)")


if __name__ == "__main__":
    main()
