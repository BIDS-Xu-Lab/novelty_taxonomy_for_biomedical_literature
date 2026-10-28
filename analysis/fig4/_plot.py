# %% shared plotting helpers for Figure 4 (citation-percentile trajectory)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SURFACE = "#ffffff"

TOP_ORDER = [
    "Concept Novelty",
    "Method and/or Material Novelty",
    "Finding Novelty",
]

# Family primaries — bright, saturated hues chosen for high visibility.
# Method's hot pink (#ff1493) must NOT blend with the tab-red accent (#b30000);
# Concept's purple must NOT blend with Method's hot pink.
FAMILY_PRIMARY = {
    "Concept Novelty":                "#9900ff",   # bright deep purple
    "Method and/or Material Novelty": "#ff0080",   # deeppink / hot pink
    "Finding Novelty":                "#00aaff",   # bright saturated blue
}
PANEL_A_ALPHA = 0.6

# tab10 with the red slot swapped for a deeper true red so it doesn't blend
# into Method's hot pink primary.
_TAB10 = ["#1f77b4", "#ff7f0e", "#2ca02c", "#b30000",
          "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
          "#bcbd22", "#17becf"]

# Per-family accent order — each list SKIPS the tab10 slot that clashes with
# the family's primary hue so two similar colours never appear in one panel.
FAMILY_ACCENTS = {
    "Concept Novelty":                [_TAB10[i] for i in (1, 2, 3, 5, 6, 8, 9)],  # skip tab-purple
    "Method and/or Material Novelty": [_TAB10[i] for i in (1, 3, 2, 4, 5, 8, 9)],  # skip tab-pink
    "Finding Novelty":                [_TAB10[i] for i in (1, 2, 3, 4, 6, 5, 8)],  # skip tab-blue + tab-cyan
}


def shade_ramp(top_name, n):
    """First curve = family primary; remaining = bright tab10 accents."""
    return [FAMILY_PRIMARY[top_name]] + FAMILY_ACCENTS[top_name][: max(0, n - 1)]


def make_pivot(df, group_col, metric, min_n=30, agg="median"):
    """Yearly `agg` (median/mean) of `metric` grouped by `group_col`; cells with n < min_n → NaN."""
    pivot = (df.groupby(["pub_year", group_col])[metric]
             .agg(agg).unstack(group_col))
    counts = (df.groupby(["pub_year", group_col]).size()
              .unstack(group_col).fillna(0).reindex(pivot.index))
    return pivot.where(counts >= min_n)


def _apply_axis_style(ax, ylim, is_leftmost, baseline=0, baseline_label="Corpus median"):
    """Only left+bottom spines; no background grid; baseline drawn as a light-
    gray dashed line at the bottom layer so it never covers data curves."""
    ax.axhline(baseline, color="#8a8a8a", linewidth=1.0, linestyle="--",
               alpha=0.7, zorder=0, label=baseline_label)
    ax.set_ylim(ylim)
    ax.set_xlabel("")
    ax.set_ylabel("")
    if not is_leftmost:
        ax.tick_params(labelleft=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _plot_series(ax, pivot, colors, labels, alpha=0.8):
    for col, color, lab in zip(pivot.columns, colors, labels):
        ax.plot(pivot.index, pivot[col].values,
                color=color, linewidth=1.2, alpha=alpha,
                marker="o", markersize=2, markeredgewidth=0, label=lab)


def _apply_legend(ax, specs):
    """Draw one or more legends on `ax` from `specs = [(loc, mode), ...]`.

    mode: None → all handles; "first_half" → first ceil(n/2); "second_half" → rest.
    """
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    n = len(handles)
    first_leg = None
    for i, (loc, mode) in enumerate(specs):
        if mode == "first_half":
            k = (n + 1) // 2
            h, l = handles[:k], labels[:k]
        elif mode == "second_half":
            k = (n + 1) // 2
            h, l = handles[k:], labels[k:]
        else:
            h, l = handles, labels
        leg = ax.legend(h, l, fontsize=8, loc=loc, framealpha=0.2)
        if i == 0:
            first_leg = leg
        else:
            ax.add_artist(first_leg)


# Figure 4 layout: 3×3 grid.  Each entry: (group_col, filter_col, filter_val, title).
# Panel 0 is special-cased — grouped by level1 across the full novelty corpus.
_FIG4_PANELS = [
    (None,     None,     None,                              "[L0] Overall"),
    ("level2", "level1", "Concept Novelty",                 "[L1] Concept Novelty"),
    ("level2", "level1", "Method and/or Material Novelty",  "[L1] Method and/or Material Novelty"),
    ("level2", "level1", "Finding Novelty",                 "[L1] Finding Novelty"),
    ("level3", "level2", "New research method",             "[L2] New research method"),
    ("level3", "level2", "New application method",          "[L2] New application method"),
    ("level3", "level2", "New object",                      "[L2] New object"),
    ("level3", "level2", "New property/feature",            "[L2] New property/feature"),
    ("level3", "level2", "New interaction",                 "[L2] New interaction"),
]

# Legend placement per panel.  Panels g/h split into two legends to keep
# 7-series panels readable without shrinking marker size.
# Per-panel colour overrides: panel_idx → {curve_position: hex_color}.
# Applied after shade_ramp() to swap specific tab10 slots on specific panels
# without touching the family-wide accent order.
_PANEL_COLOR_OVERRIDES = {
    # Panel c ([L1] Method and/or Material): New dataset/material red → green
    2: {2: "#2ca02c"},
    # Panel e ([L2] New research method): other new research method red → green
    4: {2: "#2ca02c"},
}


_LEGEND_SPEC = {
    0: [("upper left", None)],
    1: [("upper left", None)],
    2: [("upper left", None)],
    3: [("lower left", None)],
    4: [("upper left", None)],
    5: [("upper left", None)],
    6: [("upper right", None)],
    7: [("upper left", None)],
    8: [("upper right", None)],
}


def build_fig4(df, metric="delta_5yr", year_range=(1975, 2021),
               min_n=30, ylim=None, baseline=0, legend_loc=None,
               figsize=(13, 10), out_path=None, transparent=False, agg="median",
               baseline_label="Corpus median"):
    """Build the 3×3 Figure-4 grid for the given per-article metric.

    ylim: None → per-row auto-fit (row 3 gets its own wider range);
          (lo, hi) → shared global limit;
          {0: (lo, hi), 1: (lo, hi), 2: (lo, hi)} → per-row override.
    baseline: y-value of the horizontal reference line.
    legend_loc: None → use per-panel default from _LEGEND_SPEC;
                str  → same location string for every panel (e.g. "lower left").
    agg: yearly summary of the per-article metric ("median" for citation deltas;
         "mean" for patent share gaps, where the mean of a 0/1-based gap is the
         group's percentage-point difference from the corpus share).
    baseline_label: legend text for the dashed baseline.
    """
    df = df[(df["pub_year"] >= year_range[0]) & (df["pub_year"] <= year_range[1])]
    df = df[df[metric].notna()]

    face = "none" if transparent else SURFACE
    fig, axes = plt.subplots(3, 3, figsize=figsize, sharex=True, facecolor=face)
    axes = axes.flatten()
    if transparent:
        for ax in axes:
            ax.set_facecolor("none")

    # First pass: build (pivot, colors, labels) for every panel
    panels = []  # (ax_idx, row, piv, colors, labels, title)
    for j, (group_col, filt_col, filt_val, title) in enumerate(_FIG4_PANELS):
        if j == 0:
            piv = make_pivot(df[~df["is_not_novelty"]], "level1", metric, min_n=min_n, agg=agg)
            piv = piv[[c for c in TOP_ORDER if c in piv.columns]]
            colors = [FAMILY_PRIMARY[c] for c in piv.columns]
            labels = [c.replace(" Novelty", "") for c in piv.columns]
        else:
            sub = df[df[filt_col] == filt_val]
            piv = make_pivot(sub, group_col, metric, min_n=min_n, agg=agg)
            if piv.shape[1] == 0:
                axes[j].set_visible(False)
                continue
            col_order = [c for c in sub[group_col].value_counts().index if c in piv.columns]
            piv = piv[col_order]
            parent_top = filt_val if filt_col == "level1" else _lookup_top_of_level2(filt_val)
            colors = shade_ramp(parent_top, len(piv.columns))
            for pos, hex_col in _PANEL_COLOR_OVERRIDES.get(j, {}).items():
                if pos < len(colors):
                    colors[pos] = hex_col
            labels = list(piv.columns)
        panels.append((j, j // 3, piv, colors, labels, title))

    # Per-row y-lim resolution
    if ylim is None:
        def _row_range(rows):
            vals = pd.concat([p[2].stack() for p in panels if p[1] in rows])
            lo, hi = float(vals.min()), float(vals.max())
            return (int(np.floor((lo - 2) / 5) * 5),
                    int(np.ceil((hi + 2) / 5) * 5))
        row_ylim = {0: _row_range({0, 1}), 1: _row_range({0, 1}), 2: _row_range({2})}
    elif isinstance(ylim, dict):
        row_ylim = ylim
    else:
        row_ylim = {0: ylim, 1: ylim, 2: ylim}

    for (j, row, piv, colors, labels, title) in panels:
        ax = axes[j]
        _plot_series(ax, piv, colors, labels,
                     alpha=(PANEL_A_ALPHA if j == 0 else 0.8))
        _apply_axis_style(ax, row_ylim[row], is_leftmost=(j % 3 == 0), baseline=baseline,
                          baseline_label=baseline_label)
        ax.set_title(title, fontsize=10, fontweight="bold")
        spec = ([(legend_loc, None)] if legend_loc
                else _LEGEND_SPEC.get(j, [("upper left", None)]))
        _apply_legend(ax, spec)

    plt.tight_layout()

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        fig.savefig(out_path, dpi=200, bbox_inches="tight",
                    facecolor=face, transparent=transparent)
        print(f"* saved {out_path}")
    return fig, axes


# level2 → parent top-level (lazy-loaded from the taxonomy file)
_L2_TO_TOP = None
def _lookup_top_of_level2(l2_name):
    global _L2_TO_TOP
    if _L2_TO_TOP is None:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from nobl import paths
        from nobl.taxonomy import read_hierarchy
        tx = read_hierarchy(paths.TAXONOMY)
        _L2_TO_TOP = {
            second["heading"]: top["heading"]
            for top in tx for second in top.get("children", [])
        }
    return _L2_TO_TOP.get(l2_name, "Finding Novelty")
