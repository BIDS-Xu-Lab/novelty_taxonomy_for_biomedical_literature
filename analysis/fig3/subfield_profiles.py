"""Subfield novelty profiles and the three profile classes (Results §2, Fig. S1, Table S1).

Top-level shares are computed for each of the 130 Broad Subject Terms, standardised and
clustered with K-means (K = 3, random_state = 42, n_init = 10).

Inputs : derived/labels.tsv, derived/article_subfields.tsv
Outputs: outputs/fig3/top_percentage.tsv, top_percentage_clustered.tsv, table_S1.tsv,
         bar.png (Fig. S1)
"""
# %% import
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from nobl import paths
from nobl.taxonomy import get_taxonomy_df, get_top_percentage, load_labels, read_hierarchy


# %% output dir
output_dir = paths.OUTPUT_DIR / "fig3"
os.makedirs(output_dir, exist_ok=True)


# %% load
taxonomy = read_hierarchy(paths.TAXONOMY)  # 31 + 1
df_annotation = load_labels(paths.TAXONOMY, paths.LABELS)
subfields = pd.read_csv(paths.ARTICLE_SUBFIELDS, sep="\t", dtype={"pmid": str})


# %% corpus baseline (Results §1, Table S1, Fig. S1)
# corpus-wide top-level shares
baseline = get_top_percentage(get_taxonomy_df(taxonomy, df_annotation), bst="Corpus baseline")
print(f"* corpus baseline: {baseline}")


# %% tsv
output = []
for bst, pmids in sorted(subfields.groupby("bst")["pmid"]):
    df_annotation_i = df_annotation[df_annotation["pmid"].isin(set(pmids))]
    df_taxonomy_i = get_taxonomy_df(taxonomy, df_annotation_i)
    output.append(get_top_percentage(df_taxonomy_i, bst=bst))
df_output = pd.DataFrame(output)

output_fp = os.path.join(output_dir, "top_percentage.tsv")
df_output.to_csv(output_fp, sep="\t", index=False)
print(f"* saved {len(df_output)} subfields to {output_fp}")


# %% cluster
# Step 1: Load the data
output_fp = os.path.join(output_dir, "top_percentage.tsv")
df = pd.read_csv(output_fp, sep="\t")

# Step 2: Standardize the novelty features
features = ["Concept Novelty", "Finding Novelty", "Method And/Or Material Novelty"]
scaler = StandardScaler()
scaled = scaler.fit_transform(df[features])

# Step 3: KMeans clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(scaled)

# Step 4: Rename clusters and assign colors
# name each cluster by the feature that dominates its unscaled centroid (as in ternary_plot.py)
cluster_names = {"Concept Novelty": "Concept Novelty Cluster", "Finding Novelty": "Finding Novelty Cluster",
                 "Method And/Or Material Novelty": "Method and/or Material Novelty Cluster"}
centroids = scaler.inverse_transform(kmeans.cluster_centers_)
df["cluster"] = df["cluster"].map({i: cluster_names[features[centroids[i].argmax()]] for i in range(3)})
cluster_colors = {"Concept Novelty Cluster": "#D92523", "Method and/or Material Novelty Cluster": "#4CB063", "Finding Novelty Cluster": "#0072B2"}
print(f"* cluster 'Concept Novelty Cluster': {len(df[df['cluster'] == 'Concept Novelty Cluster'])}")
print(f"* cluster 'Method and/or Material Novelty Cluster': {len(df[df['cluster'] == 'Method and/or Material Novelty Cluster'])}")
print(f"* cluster 'Finding Novelty Cluster': {len(df[df['cluster'] == 'Finding Novelty Cluster'])}")

# Step 5: Calculate the mean of each feature for each cluster
df_grouped = df.groupby("cluster")[features].mean().reset_index()
print(df_grouped)

# %% bar
# Step 8: Sort the DataFrame by cluster
# First create a custom sort order for clusters
cluster_order = {
    "Concept Novelty Cluster": 0, 
    "Method and/or Material Novelty Cluster": 1, 
    "Finding Novelty Cluster": 2, 
}

# Add a cluster_order column for sorting
df["cluster_order"] = df["cluster"].map(cluster_order)

# Sort by cluster order first, then by the three novelty types in specified order
df_sorted = df.sort_values(
    by=["cluster_order", "Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"],
    ascending=[False, True, True, False]
).drop(columns=["cluster_order"]).reset_index()

# Step 9: Prepare plotting
# cluster_colors = {"Concept Novelty Cluster": "#D92523", "Method and/or Material Novelty Cluster": "#4CB063", "Finding Novelty Cluster": "#0072B2"}
labels = ["Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"]
colors = ["#cdb4db", "#ffafcc", "#a2d2ff"]

# Step 10: Horizontal Bar Plot (rotated 90 degrees)
fig, ax = plt.subplots(figsize=(10, 16))  # Swapped dimensions for horizontal layout

lefts = np.zeros(len(df_sorted))
for i, col in enumerate(labels):
    values = df_sorted[col]
    ax.barh(df_sorted.bst, values, height=1.0, edgecolor='white', left=lefts, label=col, color=colors[i])
    lefts += values

# Add color bar for clusters
for i, cluster in enumerate(df_sorted["cluster"]):
    ax.axhspan(i - 0.5, i + 0.5, xmin=-0.01, xmax=-0.03, color=cluster_colors[cluster], clip_on=False)

# Beautify
ax.set_xlabel("Novelty Percentage", fontsize=12)
ax.set_ylabel("Biomedical Subdomain", fontsize=12)
ax.set_yticks(range(len(df_sorted)))
ax.tick_params(axis='y', which='both', pad=14)  # Increase padding to move labels left
ax.yaxis.set_tick_params(labelright=False, labelleft=True)
ax.set_yticklabels(df_sorted["bst"], fontsize=8)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.03), ncol=3)
ax.set_xlim(0, 102)

# Add reference lines
# cumulative boundaries of the corpus-wide composition
ref_x = [baseline["Concept Novelty"],
         round(baseline["Concept Novelty"] + baseline["Method And/Or Material Novelty"], 2)]
ax.axvline(x=ref_x[0], color='gray', linestyle='-', alpha=0.7, linewidth=0.6)
ax.axvline(x=ref_x[1], color='gray', linestyle='-', alpha=0.7, linewidth=0.6)

# Add text annotations for the reference lines
ax.text(ref_x[0], len(df_sorted) + 0.6, f'{ref_x[0]:.2f}', ha='left', va='bottom', color='gray')
ax.text(ref_x[1], len(df_sorted) + 0.6, f'{ref_x[1]:.2f}', ha='left', va='bottom', color='gray')

# Remove the frame/border
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "bar.png"), dpi=300, bbox_inches="tight")
plt.close()


# %% cluster assignment of every subfield
df.drop(columns="cluster_order").to_csv(os.path.join(output_dir, "top_percentage_clustered.tsv"), sep="\t", index=False)


# %% Table S1: number of subfields and mean composition of each profile class, with the corpus baseline
table_s1 = df.groupby("cluster")[features].mean().round(2)
table_s1.insert(0, "n_subfields", df.groupby("cluster").size())
table_s1 = table_s1.reindex(["Concept Novelty Cluster", "Method and/or Material Novelty Cluster", "Finding Novelty Cluster"])
table_s1.loc["Corpus baseline"] = [len(df)] + [baseline[f] for f in features]
table_s1 = table_s1[["n_subfields", "Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"]]
table_s1["n_subfields"] = table_s1["n_subfields"].astype(int)
table_s1.rename_axis("profile").to_csv(os.path.join(output_dir, "table_S1.tsv"), sep="\t")
print(table_s1)
