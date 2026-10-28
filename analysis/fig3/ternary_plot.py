"""Ternary plot of the 3 top-level novelty percentages across 130 BST subfields.

Points are colored by K-means cluster (same clustering as subfield_profiles.py).
Cluster centroids are overlaid as diamonds; the global biomedical baseline
(computed from df_taxonomy.tsv) is overlaid as a star.
"""
from pathlib import Path
import math
import colorsys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgb, to_hex
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nobl import paths

OUT_DIR = paths.OUTPUT_DIR / "fig3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATA = OUT_DIR / "top_percentage.tsv"
TAXONOMY = paths.OUTPUT_DIR / "fig1" / "df_taxonomy.tsv"
OUT_FIG = OUT_DIR / "ternary.png"

FEATURES = ["Concept Novelty", "Finding Novelty", "Method And/Or Material Novelty"]
FEATURE_SHORT = ["Concept", "Finding", "Method"]

SURFACE = "#ffffff"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Purple/pink/blue base pastel, same softened-dark tone as sankey_regime.py / trajectory_* so this figure
# stays visually consistent with the rest of the results section.
CLUSTER_BASE = {
    "Concept": "#cdb4db",
    "Method":  "#ffafcc",
    "Finding": "#a2d2ff",
}


def _darken(hex_color, target_l=0.58, sat_scale=0.78):
    r, g, b = to_rgb(hex_color)
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, target_l, s * sat_scale)
    return to_hex((r2, g2, b2))


CLUSTER_COLORS = {r: _darken(c) for r, c in CLUSTER_BASE.items()}
BASELINE_COLOR = "#0b0b0b"


def tern_to_xy(c, f, m):
    """Barycentric (c, f, m) with c+f+m=1 → Cartesian. Vertices: C bottom-left, M bottom-right, F top."""
    total = c + f + m
    c, f, m = c / total, f / total, m / total
    x = m + 0.5 * f
    y = (math.sqrt(3) / 2) * f
    return x, y


def load_baseline():
    tx = pd.read_csv(TAXONOMY, sep="\t")
    grp = tx.groupby("top")["percentage"].sum()
    return (
        grp["Concept Novelty"] / 100.0,
        grp["Finding Novelty"] / 100.0,
        grp["Method And/Or Material Novelty"] / 100.0,
    )


def cluster_bsts(df):
    """Same as subfield_profiles.py: StandardScaler + KMeans(n_clusters=3, random_state=42, n_init=10)."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[FEATURES])
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    ids = kmeans.fit_predict(scaled)
    centroids_unscaled = scaler.inverse_transform(kmeans.cluster_centers_)
    id_to_name = {i: FEATURE_SHORT[centroids_unscaled[i].argmax()] for i in range(3)}
    if len(set(id_to_name.values())) != 3:
        raise RuntimeError(f"Cluster naming collided: {id_to_name}")
    df = df.copy()
    df["cluster"] = [id_to_name[i] for i in ids]
    centroids = {id_to_name[i]: centroids_unscaled[i] / 100.0 for i in range(3)}
    return df, centroids


def render(df, centroids, baseline_xy, counts):
    """Render the ternary plot."""
    S = 1
    TS = 1

    fig, ax = plt.subplots(figsize=(9.5 * S, 8.4 * S), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)

    v_c = tern_to_xy(1, 0, 0)
    v_f = tern_to_xy(0, 1, 0)
    v_m = tern_to_xy(0, 0, 1)
    triangle = Polygon([v_c, v_m, v_f], closed=True, fill=False,
                       edgecolor=AXIS, linewidth=1.2 * S, zorder=2)
    ax.add_patch(triangle)

    for t in (0.2, 0.4, 0.6, 0.8):
        p1 = tern_to_xy(t, 1 - t, 0)
        p2 = tern_to_xy(t, 0, 1 - t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.6 * S, zorder=1)
        p1 = tern_to_xy(1 - t, t, 0)
        p2 = tern_to_xy(0, t, 1 - t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.6 * S, zorder=1)
        p1 = tern_to_xy(1 - t, 0, t)
        p2 = tern_to_xy(0, 1 - t, t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.6 * S, zorder=1)

    for t in (0.2, 0.4, 0.6, 0.8):
        p = tern_to_xy(1 - t, t, 0)
        ax.annotate(f"{round((1-t)*100)}", xy=p, xytext=(-6 * S, 3 * S), textcoords="offset points",
                    fontsize=8 * S * TS, color=INK_MUTED, ha="right", va="bottom")
        p = tern_to_xy(0, 1 - t, t)
        ax.annotate(f"{round((1-t)*100)}", xy=p, xytext=(6 * S, 3 * S), textcoords="offset points",
                    fontsize=8 * S * TS, color=INK_MUTED, ha="left", va="bottom")
        p = tern_to_xy(t, 0, 1 - t)
        ax.annotate(f"{round((1-t)*100)}", xy=p, xytext=(0, -10 * S), textcoords="offset points",
                    fontsize=8 * S * TS, color=INK_MUTED, ha="center", va="top")

    dot_colors = df["cluster"].map(CLUSTER_COLORS).values
    ax.scatter(df["x"], df["y"], s=42 * S * S, c=dot_colors,
               edgecolors="none", zorder=3, alpha=0.7)

    for name, (cc, cf, cm) in centroids.items():
        cx_, cy_ = tern_to_xy(cc, cf, cm)
        # Filled diamond + a solid dark outline (drawn as an alpha=1 diamond
        # on top so the edge doesn't inherit the fill's transparency).
        ax.scatter([cx_], [cy_], s=55 * S * S, marker="D",
                   c=CLUSTER_COLORS[name], edgecolors="none",
                   zorder=5, alpha=0.7)
        ax.scatter([cx_], [cy_], s=55 * S * S, marker="D",
                   facecolors="none", edgecolors=INK_PRIMARY,
                   linewidths=0.9 * S, zorder=5.1)

    ax.scatter([baseline_xy[0]], [baseline_xy[1]], s=190 * S * S, marker="*",
               c=BASELINE_COLOR, edgecolors="none", zorder=6, alpha=0.7)

    ax.annotate("Concept", xy=v_c, xytext=(-6 * S, -10 * S), textcoords="offset points",
                fontsize=13 * S * TS, color=INK_PRIMARY, ha="right", va="top", weight="medium")
    ax.annotate("Finding", xy=v_f, xytext=(0, 12 * S), textcoords="offset points",
                fontsize=13 * S * TS, color=INK_PRIMARY, ha="center", va="bottom", weight="medium")
    ax.annotate("Method/material", xy=v_m, xytext=(6 * S, -10 * S), textcoords="offset points",
                fontsize=13 * S * TS, color=INK_PRIMARY, ha="left", va="top", weight="medium")

    ax.annotate("Concept (%)", xy=(0.22, math.sqrt(3) / 4),
                xytext=(-34 * S, 0), textcoords="offset points",
                fontsize=10 * S * TS, color=INK_SECONDARY, ha="center", va="center",
                rotation=60)
    ax.annotate("Finding (%)", xy=(0.78, math.sqrt(3) / 4),
                xytext=(34 * S, 0), textcoords="offset points",
                fontsize=10 * S * TS, color=INK_SECONDARY, ha="center", va="center",
                rotation=-60)
    ax.annotate("Method/material (%)", xy=(0.5, 0),
                xytext=(0, -26 * S), textcoords="offset points",
                fontsize=10 * S * TS, color=INK_SECONDARY, ha="center", va="center")

    # Tight offsets (~4pt) so each label sits right next to its dot.
    label_specs = {
        "Ethics":                            {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "History of Medicine":               {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Medical Informatics":               {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Chemistry Techniques, Analytical":  {"ha": "right",  "va": "bottom", "dx": -4, "dy":  3},
        "Radiotherapy":                      {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Bacteriology":                      {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Pathology":                         {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Internal Medicine":                 {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
        "Cardiology":                        {"ha": "left",   "va": "center", "dx":  4, "dy":  0},
    }
    for bst_name, spec in label_specs.items():
        row = df[df["bst"] == bst_name]
        if row.empty:
            continue
        px, py = float(row["x"].iloc[0]), float(row["y"].iloc[0])
        ax.annotate(bst_name, xy=(px, py),
                    xytext=(spec["dx"] * S, spec["dy"] * S), textcoords="offset points",
                    fontsize=8.5 * S * TS, color=INK_PRIMARY,
                    ha=spec["ha"], va=spec["va"], zorder=4,
                    bbox=dict(boxstyle=f"round,pad={0.18 * S}", fc=SURFACE, ec="none", alpha=0.82),
                    arrowprops=dict(arrowstyle="-", color=INK_SECONDARY,
                                    lw=0.5 * S, shrinkA=1, shrinkB=3.5 * S))

    legend_handles = []
    for name in ("Concept", "Method", "Finding"):
        n = counts.get(name, 0)
        legend_handles.append(
            Line2D([0], [0], marker="o", linestyle="", markersize=8 * S,
                   markerfacecolor=CLUSTER_COLORS[name], markeredgecolor="none",
                   alpha=0.7,
                   label=f"{name}-oriented fields  (n={n})")
        )
    legend_handles.append(
        Line2D([0], [0], marker="D", linestyle="", markersize=9 * S,
               markerfacecolor="#9a9a9a",
               markeredgecolor=INK_PRIMARY, markeredgewidth=0.9 * S,
               alpha=0.7,
               label="Cluster centroid")
    )
    legend_handles.append(
        Line2D([0], [0], marker="*", linestyle="", markersize=12 * S,
               markerfacecolor=BASELINE_COLOR, markeredgecolor="none",
               alpha=0.7,
               label="Global biomedical baseline")
    )
    ax.legend(handles=legend_handles, loc="upper left", frameon=False,
              fontsize=9 * S * TS, labelcolor=INK_PRIMARY, borderaxespad=0.2,
              bbox_to_anchor=(-0.02, 1.02))

    ax.set_xlim(-0.18, 1.24)
    ax.set_ylim(-0.10, math.sqrt(3) / 2 + 0.12)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


def main():
    df = pd.read_csv(DATA, sep="\t")
    df.columns = [c.strip() for c in df.columns]
    df["c"] = df[FEATURES[0]] / 100.0
    df["f"] = df[FEATURES[1]] / 100.0
    df["m"] = df[FEATURES[2]] / 100.0

    df, centroids = cluster_bsts(df)

    xs, ys = zip(*[tern_to_xy(c, f, m) for c, f, m in zip(df["c"], df["f"], df["m"])])
    df["x"], df["y"] = xs, ys

    baseline_c, baseline_f, baseline_m = load_baseline()
    baseline_xy = tern_to_xy(baseline_c, baseline_f, baseline_m)

    counts = df["cluster"].value_counts().to_dict()
    print(f"cluster counts: {counts}")
    print(f"baseline (c, f, m): {baseline_c:.4f}, {baseline_f:.4f}, {baseline_m:.4f}")

    fig = render(df, centroids, baseline_xy, counts)
    fig.savefig(OUT_FIG, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {OUT_FIG}")


if __name__ == "__main__":
    main()
