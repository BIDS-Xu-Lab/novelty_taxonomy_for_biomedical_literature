# %% per-article citation DELTA vs the corpus median that year
# Rationale: external baselines (full PubMed or conclusion-bearing PubMed) are
# confounded by composition shifts (abstract-availability rise; new-entry
# journal expansion post-2000).  Subtracting the yearly median of the same
# 2.37M keyword-filtered corpus keeps the reference pool constant across
# numerator and denominator, so between-type differences are apples-to-apples.
#
# Inputs : derived/citations.parquet, derived/labels.tsv (2.37M novelty corpus pmids)
# Output : outputs/fig4/novelty_percentile.parquet
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from nobl import paths
from nobl.taxonomy import read_hierarchy, load_labels

FP_CITATIONS = paths.CITATIONS
FP_TAXONOMY = paths.TAXONOMY
FP_ANNOTATION = paths.LABELS
OUT_DIR = paths.OUTPUT_DIR / "fig4"
os.makedirs(OUT_DIR, exist_ok=True)

YEAR_MIN, YEAR_MAX = 1975, 2024
# Raw metrics used downstream:
#   citations_5yr      — fixed 5-year window (age-invariant); primary
#   citations_total    — unbounded, accumulates with paper age
#   citations_per_year — total / years_since_pub (rate; normalizes age across years)
METRICS = ["citations_5yr", "citations_total", "citations_per_year"]


# %% load 2.37M corpus with taxonomy levels
def get_leaf_to_levels(taxonomy):
    out = {}
    for top in taxonomy:
        l1 = top["heading"]
        for second in top.get("children", []):
            l2 = second["heading"]
            if not second.get("children"):
                out[second["heading"].lower()] = (l1, l2)
            for third in second.get("children", []):
                out[third["heading"].lower()] = (l1, l2)
    return out


taxonomy = read_hierarchy(FP_TAXONOMY)
leaf_to_levels = get_leaf_to_levels(taxonomy)

df_ann = load_labels(FP_TAXONOMY, FP_ANNOTATION)
df_ann["pmid"] = df_ann["pmid"].astype("int64")
df_ann["level1"] = df_ann["output"].map(
    lambda x: leaf_to_levels.get(x, ("not novelty", "not novelty"))[0]
)
df_ann["level2"] = df_ann["output"].map(
    lambda x: leaf_to_levels.get(x, ("not novelty", "not novelty"))[1]
)
df_ann["level3"] = df_ann["output"]
df_ann["is_not_novelty"] = df_ann["output"].eq("not novelty")


# %% merge citations restricted to corpus pmids
print("* loading citations for corpus pmids only ...")
cit = pd.read_parquet(FP_CITATIONS)
cit = cit[(cit["pub_year"] >= YEAR_MIN) & (cit["pub_year"] <= YEAR_MAX)].copy()
cit["pmid"] = cit["pmid"].astype("int64")

df = df_ann.merge(cit, on="pmid", how="inner")
print(f"* corpus rows matched to citations: {len(df):,} / {len(df_ann):,}")


# %% per-article delta vs the corpus median that year
#     delta = article_citation - corpus_median_that_year
for m in METRICS:
    year_med = df.groupby("pub_year")[m].transform("median")
    delta_col = f"delta_{m.replace('citations_', '')}"
    df[delta_col] = (df[m] - year_med).astype("float32")


# %% save
keep = ["pmid", "pub_year",
        "level1", "level2", "level3", "is_not_novelty",
        "citations_5yr", "citations_total", "citations_per_year",
        "delta_5yr", "delta_total", "delta_per_year"]
fp_out = os.path.join(OUT_DIR, "novelty_percentile.parquet")
df[keep].to_parquet(fp_out, index=False)
print(f"* saved {fp_out} ({len(df):,} rows)")

