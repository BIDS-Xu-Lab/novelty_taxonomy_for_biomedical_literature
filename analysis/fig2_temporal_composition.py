"""Temporal composition of claimed novelty, 1975–2024 (Fig. 2).

Annual prevalence = claims in a category / all mapped novelty claims that year.

Inputs : derived/labels.tsv, derived/labels_with_year.parquet
Outputs: outputs/fig2/top_percentage.tsv, top_stacked_bars.png                         (Fig. 2a)
         outputs/fig2/leaf_percentage.tsv, leaf_stacked_bars.png                        (Fig. 2b)
         outputs/fig2/leaf_individual_bars.png, leaf_peak_years.tsv                     (Fig. 2c)
"""
# %% load
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nobl import paths
from nobl.taxonomy import get_taxonomy_df, get_top_percentage, load_labels, read_hierarchy

START_YEAR, END_YEAR = 1975, 2024
MIN_PER_YEAR = 100  # Fig. 2a skips years with fewer classified conclusions

output_dir = paths.OUTPUT_DIR / "fig2"
output_dir.mkdir(parents=True, exist_ok=True)

df_with_meta = pd.read_parquet(paths.LABELS_WITH_YEAR, columns=["pmid", "year"])
df_with_meta["pmid"] = df_with_meta["pmid"].astype(str)
taxonomy = read_hierarchy(paths.TAXONOMY)
df_annotation = load_labels(paths.TAXONOMY, paths.LABELS)


# %% top-level shares per year (Fig. 2a)
output = []
for year in range(START_YEAR, int(df_with_meta.year.max()) + 1):
    pmids = df_with_meta[df_with_meta.year == year]['pmid'].tolist()
    if len(pmids) < MIN_PER_YEAR:
        continue
    df_annotation_i = df_annotation[df_annotation['pmid'].isin(pmids)]
    df_taxonomy_i = get_taxonomy_df(taxonomy, df_annotation_i)
    output.append(get_top_percentage(df_taxonomy_i, bst=year))
df_output = pd.DataFrame(output)
df_output.to_csv(output_dir / "top_percentage.tsv", sep="\t", index=False)

labels = ["Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"]
colors = ["#cdb4db", "#ffafcc", "#a2d2ff"]

fig, ax = plt.subplots(figsize=(10, 10))
bottoms = np.zeros(len(df_output))
for i, col in enumerate(labels):
    ax.bar(df_output.bst, df_output[col], width=1.0, edgecolor='white', bottom=bottoms, label=col, color=colors[i])
    bottoms += df_output[col]
ax.set_xlabel("Years", fontsize=12)
ax.set_ylabel("Novelty Percentage", fontsize=12)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.03), ncol=3)
ax.set_ylim(0, 102)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(output_dir / "top_stacked_bars.png", dpi=300, bbox_inches="tight")
plt.close()


# %% leaf shares per year (Fig. 2b–c)
df = df_with_meta.merge(df_annotation, on="pmid", how="left")[["year", "output"]].dropna()
df["year"] = df["year"].astype(int)
df = df[(df["year"] >= START_YEAR) & (df["year"] <= END_YEAR)]
df_novelty = df[df["output"] != "not novelty"]
print(f"* {len(df_novelty)}/{len(df)} mapped novelty claims in {START_YEAR}-{END_YEAR}")

novelty_order = [
    "concept novelty", "new attempt", "new perspective", "new theory",
    "method and/or material novelty", "new research method", "new experimental method", "new data analysis method",
    "other new research method", "new application method", "new therapy", "new indicator/index/predictor",
    "new tool/device", "method reapplication/method combination", "other new application method", "new dataset/material",
    "finding novelty", "new object", "new substance", "new sequence", "new gene", "new protein", "new genus and species",
    "new case", "other new object", "new property/feature", "new cell property", "new candidate gene", "new marker",
    "new risk variant", "new biomedical function", "new target", "other new property/feature", "new interaction",
    "new pathway", "new mechanism", "new association", "other new interaction", "other new finding",
]
novelty_order_dict = {category: idx for idx, category in enumerate(novelty_order)}

share = (
    df_novelty.groupby(["year", "output"]).size()
    .reset_index(name="count")
    .assign(pct=lambda d: d.groupby("year")["count"].transform(lambda x: x / x.sum()))
)
share = share.sort_values(["year", "output"], key=lambda x: x.map(novelty_order_dict) if x.name == "output" else x)
share.to_csv(output_dir / "leaf_percentage.tsv", sep="\t", index=False)

pivot = share.pivot(index="year", columns="output", values="pct").fillna(0) * 100
pivot = pivot[[col for col in novelty_order if col in pivot.columns]]

# year of highest prevalence for each leaf (Fig. 2c)
peaks = pd.DataFrame({"peak_year": pivot.idxmax(), "peak_pct": pivot.max().round(3)})
peaks.rename_axis("output").to_csv(output_dir / "leaf_peak_years.tsv", sep="\t")

base_colors = [
    '#cdb4db', '#ffafcc', '#a2d2ff', '#bde0fe', '#ffc6ff', '#a0c4ff', '#ffd4b2', '#ffb3ba',
    '#ff9a9e', '#fecfef', '#fecfef', '#fad0c4', '#ffd1ff', '#a8e6cf', '#dcedc1', '#ffd3b6',
    '#ffaaa5', '#ff8b94', '#ffc3a0', '#ffb3ba', '#c7ceea', '#b5e7a0', '#ffb347', '#ffcc5c',
    '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd',
]
n_categories = len(pivot.columns)
category_colors = colors if n_categories <= 3 else base_colors[:n_categories]

n_cols = 3
n_rows = (n_categories + n_cols - 1) // n_cols
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 3 * n_rows), squeeze=False)
for i, (col, color) in enumerate(zip(pivot.columns, category_colors)):
    ax = axes[i // n_cols, i % n_cols]
    values = pivot[col]
    ax.bar(values.index, values.values, width=0.8, edgecolor='white', color=color, alpha=0.8)
    ax.plot(values.index, values.values, color=tuple(np.array(mcolors.to_rgb(color)) * 0.85),
            linewidth=2.5, marker='o', markersize=6)
    ax.set_ylim(0, max(values.values) * 1.1)
    ax.set_xlabel(f"{col}", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
for i in range(n_categories, n_rows * n_cols):
    axes[i // n_cols, i % n_cols].set_visible(False)
plt.tight_layout()
plt.savefig(output_dir / "leaf_individual_bars.png", dpi=300, bbox_inches="tight")
plt.close()

fig, ax = plt.subplots(figsize=(12, 10))
bottoms = np.zeros(len(pivot))
for col, color in zip(pivot.columns, category_colors):
    ax.bar(pivot.index, pivot[col].values, width=0.8, edgecolor='white', bottom=bottoms, label=col, color=color, alpha=0.8)
    bottoms += pivot[col].values
# category names beside the right-most bar
rightmost_year = pivot.index[-1]
bottom_pos = 0.0
for col, color in zip(pivot.columns, category_colors):
    last = pivot[col].iloc[-1]
    ax.text(rightmost_year + 1, bottom_pos + last / 2, col, ha='left', va='center', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor=color))
    bottom_pos += last
ax.set_xlabel("Years", fontsize=14)
ax.set_ylabel("Novelty Percentage (%)", fontsize=14)
ax.set_ylim(0, 102)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(output_dir / "leaf_stacked_bars.png", dpi=300, bbox_inches="tight")
plt.close()
