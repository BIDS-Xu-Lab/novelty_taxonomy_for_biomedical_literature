"""Trajectory overlay — colour-depth decade ramp on the purple/pink/blue palette.

Palette matches Fig. S1:
  Concept  #cdb4db (purple)  — 00s is the base tone
  Method   #ffafcc (pink)    — 80s/90s lighter, 10s/20s darker
  Finding  #a2d2ff (blue)

All marks are drawn opaque; the ramp itself carries time.

Output: trajectory_overlay_all.png (Fig. 3b, highlights added by hand)
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
OUT_FIG = OUT_DIR / "trajectory_overlay_all.png"

DECADE_ORDER = ["1980s", "1990s", "2000s", "2010s", "2020-2024"]
DECADE_SHORT = {"1980s": "80s", "1990s": "90s", "2000s": "00s",
                "2010s": "10s", "2020-2024": "20s"}
REGIMES = ["Concept", "Method", "Finding"]
REGIME_BASE = {
    "Concept": "#cdb4db",
    "Method":  "#ffafcc",
    "Finding": "#a2d2ff",
}
# Target HLS lightness per decade — a monotone ramp centred on the base tone.
DECADE_L_TARGET = {
    "1980s":     0.92,
    "1990s":     0.86,
    "2000s":     None,     # keep base lightness (unchanged)
    "2010s":     0.50,
    "2020-2024": 0.32,
}
INK_PRIMARY = "#1a1a1a"
INK_SECONDARY = "#4a4a4a"
INK_MUTED = "#8a8a8a"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#ffffff"


def relight(hex_color, target_l):
    """Return the hex you get by changing this colour's HLS lightness to target_l."""
    if target_l is None:
        return hex_color
    r, g, b = to_rgb(hex_color)
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, target_l, s)
    return to_hex((r2, g2, b2))


# Build the (regime, decade) → hex table once.
REGIME_DECADE_COLORS = {
    r: {d: relight(REGIME_BASE[r], DECADE_L_TARGET[d]) for d in DECADE_ORDER}
    for r in REGIMES
}


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


def collect_pts(sub):
    pts = []
    for d in DECADE_ORDER:
        row = sub[sub["decade"] == d]
        if row.empty:
            continue
        c = row["Concept %"].iloc[0] / 100
        f = row["Finding %"].iloc[0] / 100
        m = row["Method And/Or Material %"].iloc[0] / 100
        reg = row["regime"].iloc[0]
        pts.append({"d": d, **dict(zip("xy", tern_to_xy(c, f, m))), "reg": reg})
    return pts


def get_all_bsts(df):
    pv = df.pivot(index="bst", columns="decade", values="regime").reindex(columns=DECADE_ORDER)
    return [b for b, row in pv.iterrows() if row.dropna().size >= 2]


def render_overlay(ax, df, bsts):
    draw_triangle(ax)

    n_seg = 60
    for bst in bsts:
        pts = collect_pts(df[df["bst"] == bst])
        if not pts:
            continue

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
            color = REGIME_DECADE_COLORS[pt["reg"]][pt["d"]]
            ax.scatter([pt["x"]], [pt["y"]], s=22, c=color,
                       edgecolors=SURFACE, linewidths=0.4,
                       zorder=5)

    ax.set_xlim(-0.10, 1.10)
    ax.set_ylim(-0.08, math.sqrt(3) / 2 + 0.09)
    ax.set_aspect("equal")
    ax.axis("off")


def build_depth_legend(ax):
    """Show the 5 depth swatches per regime (a 3×5 grid in the corner)."""
    y0 = math.sqrt(3) / 2 + 0.05
    x0 = -0.05
    row_gap = 0.030
    swatch_w = 0.055
    for row_i, r in enumerate(("Concept", "Method", "Finding")):
        y = y0 - row_i * row_gap
        for i, d in enumerate(DECADE_ORDER):
            ax.add_patch(plt.Rectangle(
                (x0 + i * swatch_w, y), swatch_w, 0.024,
                facecolor=REGIME_DECADE_COLORS[r][d],
                edgecolor=SURFACE, linewidth=0.4, zorder=6))
        ax.text(x0 - 0.010, y + 0.012, r[0], fontsize=7,
                color=REGIME_DECADE_COLORS[r]["2020-2024"],
                ha="right", va="center", weight="medium", zorder=6)
    y_lab = y0 - 2 * row_gap - 0.010
    for i, d in enumerate(DECADE_ORDER):
        ax.text(x0 + i * swatch_w + swatch_w / 2, y_lab, DECADE_SHORT[d],
                fontsize=6.5, color=INK_SECONDARY, ha="center", va="top",
                zorder=6)


def main():
    df = pd.read_csv(TIMELINE, sep="\t")
    bsts = get_all_bsts(df)
    print(f"overlaying {len(bsts)} subfields")

    fig, ax = plt.subplots(figsize=(9, 8), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    render_overlay(ax, df, bsts)
    build_depth_legend(ax)
    fig.suptitle(f"All {len(bsts)} subfields — colour-depth decade ramp",
                 fontsize=12, x=0.02, y=0.98, ha="left",
                 color=INK_PRIMARY, weight="medium")
    fig.savefig(OUT_FIG, dpi=220, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {OUT_FIG}")


if __name__ == "__main__":
    main()
