"""Cumulative decade snapshots — each panel accumulates every decade up to it.

Panel 1 (1980s): only the 80s points.
Panel 2 (1990s): 80s + 90s points + gradient line 80s→90s.
Panel 3 (2000s): 80s + 90s + 00s points + gradient lines.
… panel 5 = the full trajectory_overlay_all.py view.

Uses the same regime-hue + decade-alpha gradient as trajectory_overlay_all.py.

Output: trajectory_snapshot_cum_combined.png (Fig. S3)
"""
from pathlib import Path
import math
import colorsys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb, to_hex

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nobl import paths

OUT_DIR = paths.OUTPUT_DIR / "fig3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TIMELINE = OUT_DIR / "regime_timeline.tsv"

DECADE_ORDER = ["1980s", "1990s", "2000s", "2010s", "2020-2024"]
DECADE_SHORT = {"1980s": "80s", "1990s": "90s", "2000s": "00s",
                "2010s": "10s", "2020-2024": "20s"}
DECADE_DISPLAY = {"2020-2024": "2020s"}
# Purple/pink/blue palette of Fig. S1 + HLS-lightness ramp per decade.
REGIMES = ["Concept", "Method", "Finding"]
REGIME_BASE = {
    "Concept": "#cdb4db",
    "Method":  "#ffafcc",
    "Finding": "#a2d2ff",
}
DECADE_L_TARGET = {
    "1980s":     0.92,
    "1990s":     0.86,
    "2000s":     None,     # keep base
    "2010s":     0.50,
    "2020-2024": 0.32,
}


def relight(hex_color, target_l):
    if target_l is None:
        return hex_color
    r, g, b = to_rgb(hex_color)
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, target_l, s)
    return to_hex((r2, g2, b2))


REGIME_DECADE_COLORS = {
    r: {d: relight(REGIME_BASE[r], DECADE_L_TARGET[d]) for d in DECADE_ORDER}
    for r in REGIMES
}
INK_PRIMARY = "#1a1a1a"
INK_SECONDARY = "#4a4a4a"
INK_MUTED = "#8a8a8a"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"


def tern_to_xy(c, f, m):
    total = c + f + m
    c, f, m = c / total, f / total, m / total
    x = m + 0.5 * f
    y = (math.sqrt(3) / 2) * f
    return x, y


def draw_triangle(ax):
    v_c = tern_to_xy(1, 0, 0)
    v_f = tern_to_xy(0, 1, 0)
    v_m = tern_to_xy(0, 0, 1)
    ax.add_patch(Polygon([v_c, v_m, v_f], closed=True, fill=False,
                         edgecolor=AXIS, linewidth=1.1, zorder=2))
    for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        p1 = tern_to_xy(t, 1 - t, 0);   p2 = tern_to_xy(t, 0, 1 - t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.5, zorder=1)
        p1 = tern_to_xy(1 - t, t, 0);   p2 = tern_to_xy(0, t, 1 - t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.5, zorder=1)
        p1 = tern_to_xy(1 - t, 0, t);   p2 = tern_to_xy(0, 1 - t, t)
        ax.plot(*zip(p1, p2), color=GRID, linewidth=0.5, zorder=1)
    ax.annotate("Concept", xy=v_c, xytext=(-4, -8), textcoords="offset points",
                fontsize=10, color=INK_SECONDARY, ha="right", va="top", weight="medium")
    ax.annotate("Finding", xy=v_f, xytext=(0, 8), textcoords="offset points",
                fontsize=10, color=INK_SECONDARY, ha="center", va="bottom", weight="medium")
    ax.annotate("Method", xy=v_m, xytext=(4, -8), textcoords="offset points",
                fontsize=10, color=INK_SECONDARY, ha="left", va="top", weight="medium")


def build_gradient_legend(ax, cutoff_idx):
    """Colour-depth swatches per regime; dim decades past the cutoff."""
    y0 = math.sqrt(3) / 2 + 0.05
    x0 = -0.05
    row_gap = 0.030
    swatch_w = 0.055
    for row_i, r in enumerate(("Concept", "Method", "Finding")):
        y = y0 - row_i * row_gap
        for i, d in enumerate(DECADE_ORDER):
            active = (i <= cutoff_idx)
            ax.add_patch(plt.Rectangle(
                (x0 + i * swatch_w, y), swatch_w, 0.024,
                facecolor=REGIME_DECADE_COLORS[r][d],
                alpha=1.0 if active else 0.15,
                edgecolor=SURFACE, linewidth=0.4, zorder=6))
        ax.text(x0 - 0.010, y + 0.012, r[0], fontsize=7,
                color=REGIME_DECADE_COLORS[r]["2020-2024"],
                ha="right", va="center", weight="medium", zorder=6)
    y_lab = y0 - 2 * row_gap - 0.010
    for i, d in enumerate(DECADE_ORDER):
        active = (i <= cutoff_idx)
        ax.text(x0 + i * swatch_w + swatch_w / 2, y_lab, DECADE_SHORT[d],
                fontsize=6.5,
                color=INK_SECONDARY if active else "#c8c8c8",
                ha="center", va="top", zorder=6)


def render_cumulative(ax, df, cutoff_decade):
    draw_triangle(ax)

    cutoff_idx = DECADE_ORDER.index(cutoff_decade)
    active_decades = DECADE_ORDER[: cutoff_idx + 1]

    n_seg = 60

    # Iterate one BST at a time so we can draw the incremental trajectory.
    for bst, sub in df.groupby("bst"):
        pts = []
        for d in active_decades:
            row = sub[sub["decade"] == d]
            if row.empty:
                continue
            c = row["Concept %"].iloc[0] / 100
            f = row["Finding %"].iloc[0] / 100
            m = row["Method And/Or Material %"].iloc[0] / 100
            reg = row["regime"].iloc[0]
            x, y = tern_to_xy(c, f, m)
            pts.append({"d": d, "x": x, "y": y, "reg": reg})

        if not pts:
            continue

        # Gradient lines between consecutive active-decade observations
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            c_a = np.array([*to_rgb(REGIME_DECADE_COLORS[a["reg"]][a["d"]]), 1.0])
            c_b = np.array([*to_rgb(REGIME_DECADE_COLORS[b["reg"]][b["d"]]), 1.0])
            xs = np.linspace(a["x"], b["x"], n_seg + 1)
            ys = np.linspace(a["y"], b["y"], n_seg + 1)
            segments = np.stack([np.column_stack([xs[:-1], ys[:-1]]),
                                  np.column_stack([xs[1:], ys[1:]])], axis=1)
            t = (np.arange(n_seg) + 0.5) / n_seg
            colors = c_a[None, :] + (c_b - c_a)[None, :] * t[:, None]
            lc = LineCollection(segments, colors=colors, linewidth=0.85,
                                capstyle="butt", antialiased=True, zorder=4)
            ax.add_collection(lc)

        for pt in pts:
            ax.scatter([pt["x"]], [pt["y"]], s=22,
                       c=REGIME_DECADE_COLORS[pt["reg"]][pt["d"]],
                       edgecolors=SURFACE, linewidths=0.4,
                       zorder=5)

    ax.set_xlim(-0.10, 1.10)
    ax.set_ylim(-0.08, math.sqrt(3) / 2 + 0.11)
    ax.set_aspect("equal")
    ax.axis("off")

    label = DECADE_DISPLAY.get(cutoff_decade, cutoff_decade)
    ax.text(0.5, math.sqrt(3) / 2 + 0.05,
            f"through {label}",
            transform=ax.transData, ha="center", va="bottom",
            fontsize=12, color=INK_PRIMARY, weight="medium")

    build_gradient_legend(ax, cutoff_idx)


def main():
    df = pd.read_csv(TIMELINE, sep="\t")

    fig, axes = plt.subplots(1, 5, figsize=(30, 7.4), facecolor=SURFACE)
    for ax, decade in zip(axes, DECADE_ORDER):
        ax.set_facecolor(SURFACE)
        render_cumulative(ax, df, decade)
    fig.suptitle("Cumulative subfield trajectories — decade by decade",
                 fontsize=14, x=0.02, y=0.99, ha="left",
                 color=INK_PRIMARY, weight="medium")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = OUT_DIR / "trajectory_snapshot_cum_combined.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
