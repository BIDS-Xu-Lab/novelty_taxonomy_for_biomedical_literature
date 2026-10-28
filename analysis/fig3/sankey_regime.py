"""Sankey of subfield innovation regimes across decades.

Uses the purple/pink/blue palette of Fig. S1:
  Concept  #cdb4db (purple)
  Method   #ffafcc (pink)
  Finding  #a2d2ff (light blue)

Ribbons keep the base pastel hue at RIBBON_ALPHA; blocks and text use a
softened darker version so counts stay legible on white.

Output: sankey_regime.png (Fig. 3a)
"""
from pathlib import Path
import colorsys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from matplotlib.colors import to_rgb, to_hex

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nobl import paths

OUT_DIR = paths.OUTPUT_DIR / "fig3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DECADE_ORDER = ["1980s", "1990s", "2000s", "2010s", "2020-2024"]
DECADE_DISPLAY = {"2020-2024": "2020s"}
REGIMES = ["Concept", "Method", "Finding"]
# Ribbon (flow) colour = base pastel
REGIME_COLORS = {
    "Concept": "#cdb4db",
    "Method":  "#ffafcc",
    "Finding": "#a2d2ff",
}


def _darken(hex_color, target_l=0.58, sat_scale=0.78):
    """Return the same-hue colour at HLS lightness target_l with saturation
    softly dialled down — used for block bars and text labels so they read
    clearly on white without looking neon."""
    r, g, b = to_rgb(hex_color)
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, target_l, s * sat_scale)
    return to_hex((r2, g2, b2))


# Block-bar / label colour = a softened dark tone.
REGIME_BAR_COLORS = {r: _darken(c) for r, c in REGIME_COLORS.items()}
INK_PRIMARY = "#1a1a1a"
INK_SECONDARY = "#4a4a4a"
INK_MUTED = "#8a8a8a"
SURFACE = "#ffffff"

COL_WIDTH = 0.16
COL_GAP = 3.0
REGIME_GAP = 5.5
RIBBON_ALPHA = 0.60
BAR_ALPHA = 1.00

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": INK_MUTED,
    "axes.linewidth": 0.6,
})


def bezier_ribbon(x0, x1, y0_top, y0_bot, y1_top, y1_bot, color, alpha):
    dx = (x1 - x0) * 0.5
    verts = [
        (x0, y0_top),
        (x0 + dx, y0_top), (x1 - dx, y1_top), (x1, y1_top),
        (x1, y1_bot),
        (x1 - dx, y1_bot), (x0 + dx, y0_bot), (x0, y0_bot),
        (x0, y0_top),
    ]
    codes = [MplPath.MOVETO,
             MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO,
             MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CLOSEPOLY]
    return PathPatch(MplPath(verts, codes),
                     facecolor=color, edgecolor="none", alpha=alpha,
                     antialiased=True, zorder=1)


def render(timeline_path, out_path, subtitle):
    df = pd.read_csv(timeline_path, sep="\t")
    df = df[df["decade"].isin(DECADE_ORDER)]
    timeline = df.pivot(index="bst", columns="decade", values="regime").reindex(columns=DECADE_ORDER)

    col_x = {d: i * COL_GAP for i, d in enumerate(DECADE_ORDER)}

    blocks = {}
    max_y = 0.0
    for d in DECADE_ORDER:
        col = timeline[d].dropna()
        y_cursor = 0.0
        for r in REGIMES:
            bsts_in_r = sorted(col[col == r].index.tolist())
            n = len(bsts_in_r)
            if n == 0:
                blocks[(d, r)] = (y_cursor, y_cursor, {})
                y_cursor += REGIME_GAP
                continue
            y_bot = y_cursor
            y_top = y_cursor + n
            per_bst = {bst: (y_bot + i, y_bot + i + 1) for i, bst in enumerate(bsts_in_r)}
            blocks[(d, r)] = (y_bot, y_top, per_bst)
            y_cursor = y_top + REGIME_GAP
            max_y = max(max_y, y_top)

    fig = plt.figure(figsize=(12, 7.2), facecolor=SURFACE)
    ax = fig.add_axes([0.11, 0.11, 0.78, 0.72])
    ax.set_facecolor(SURFACE)

    for d in DECADE_ORDER:
        x = col_x[d]
        for r in REGIMES:
            y_bot, y_top, _ = blocks[(d, r)]
            if y_top > y_bot:
                ax.fill_betweenx([y_bot, y_top], x - COL_WIDTH / 2, x + COL_WIDTH / 2,
                                 color=REGIME_BAR_COLORS[r], alpha=BAR_ALPHA, edgecolor="none",
                                 zorder=3)

    for i in range(len(DECADE_ORDER) - 1):
        d0, d1 = DECADE_ORDER[i], DECADE_ORDER[i + 1]
        x0 = col_x[d0] + COL_WIDTH / 2
        x1 = col_x[d1] - COL_WIDTH / 2
        pairs = timeline[[d0, d1]].dropna()

        src_cursor = {(d0, r): blocks[(d0, r)][0] for r in REGIMES}
        dst_cursor = {(d1, r): blocks[(d1, r)][0] for r in REGIMES}

        mover_labels = []
        for from_r in REGIMES:
            for to_r in REGIMES:
                subset = pairs[(pairs[d0] == from_r) & (pairs[d1] == to_r)]
                n = len(subset)
                if n == 0:
                    continue
                y0_bot = src_cursor[(d0, from_r)]
                y0_top = y0_bot + n
                y1_bot = dst_cursor[(d1, to_r)]
                y1_top = y1_bot + n
                ax.add_patch(bezier_ribbon(x0, x1,
                                           y0_top, y0_bot,
                                           y1_top, y1_bot,
                                           REGIME_COLORS[from_r], RIBBON_ALPHA))
                src_cursor[(d0, from_r)] = y0_top
                dst_cursor[(d1, to_r)] = y1_top

                if from_r != to_r:
                    x_mid = 0.5 * (x0 + x1)
                    y_mid = 0.25 * (y0_top + y0_bot + y1_top + y1_bot)
                    mover_labels.append((x_mid, y_mid, n, from_r))

        for x_mid, y_mid, n, from_r in mover_labels:
            ax.text(x_mid, y_mid, f"{n}",
                    ha="center", va="center",
                    fontsize=9, color=REGIME_BAR_COLORS[from_r], weight="bold",
                    zorder=6)

    for d in DECADE_ORDER:
        x = col_x[d]
        for r in REGIMES:
            y_bot, y_top, _ = blocks[(d, r)]
            n = int(y_top - y_bot)
            if n == 0:
                continue
            ax.text(x, y_top + 0.9, f"{n}",
                    ha="center", va="bottom",
                    fontsize=9.5, color=REGIME_BAR_COLORS[r], weight="bold", zorder=4)

    for side, d in (("left", DECADE_ORDER[0]), ("right", DECADE_ORDER[-1])):
        x = col_x[d]
        if side == "left":
            xlab = x - COL_WIDTH / 2 - 0.20
            ha = "right"
        else:
            xlab = x + COL_WIDTH / 2 + 0.20
            ha = "left"
        for r in REGIMES:
            y_bot, y_top, _ = blocks[(d, r)]
            if y_top > y_bot:
                ax.text(xlab, (y_bot + y_top) / 2, f"{r}-oriented",
                        ha=ha, va="center", fontsize=10.5,
                        color=REGIME_BAR_COLORS[r], weight="bold")

    y_baseline = -3.2
    ax.plot([col_x[DECADE_ORDER[0]], col_x[DECADE_ORDER[-1]]],
            [y_baseline, y_baseline], color=INK_MUTED, linewidth=0.7, zorder=2)
    for d in DECADE_ORDER:
        x = col_x[d]
        ax.plot([x, x], [y_baseline, y_baseline + 0.5], color=INK_MUTED, linewidth=0.7)
        ax.text(x, y_baseline - 1.2, DECADE_DISPLAY.get(d, d),
                ha="center", va="top",
                fontsize=11, color=INK_PRIMARY, weight="medium")

    fig.text(0.11, 0.94,
             "Subfield innovation regimes across decades",
             fontsize=14, color=INK_PRIMARY, weight="medium", ha="left", va="top")
    fig.text(0.11, 0.905, subtitle,
             fontsize=9.5, color=INK_SECONDARY, ha="left", va="top")

    ax.set_xlim(col_x[DECADE_ORDER[0]] - COL_WIDTH - 1.6,
                col_x[DECADE_ORDER[-1]] + COL_WIDTH + 2.6)
    ax.set_ylim(y_baseline - 2.5, max_y + 4.5)
    ax.axis("off")

    fig.savefig(out_path, dpi=220, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"wrote {out_path}")


def main():
    df_tl = pd.read_csv(OUT_DIR / "regime_timeline.tsv", sep="\t")
    n_bsts = df_tl["bst"].nunique()
    pv = df_tl.pivot(index="bst", columns="decade", values="regime").reindex(columns=DECADE_ORDER)
    total_trans, stable_trans = 0, 0
    for i in range(len(DECADE_ORDER) - 1):
        pair = pv[[DECADE_ORDER[i], DECADE_ORDER[i + 1]]].dropna()
        total_trans += len(pair)
        stable_trans += (pair.iloc[:, 0] == pair.iloc[:, 1]).sum()
    stability = 100 * stable_trans / total_trans

    subtitle = (f"{n_bsts} biomedical subject terms, cells with ≥100 novelty claims. "
                f"Ribbon colour = source regime; overall stability {stability:.1f}%.")
    render(OUT_DIR / "regime_timeline.tsv",
           OUT_DIR / "sankey_regime.png",
           subtitle)


if __name__ == "__main__":
    main()
