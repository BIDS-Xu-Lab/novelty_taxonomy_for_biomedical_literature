# %% Figs. S4–S6 — median citation-count DELTA vs the per-year corpus median.
#
# Fig. 4 in the main text shows seven of the nine Fig. S4 panels; its layout, hierarchy
# guide and peak shading were finished by hand.
#
# Three metric variants:
#   delta_5yr      — 5-yr window; age-invariant; primary
#   delta_total    — total citations (unbounded, grows with paper age)
#   delta_per_year — citations per year of paper existence (rate; normalizes
#                    for paper age across years — old-year deltas are divided
#                    by ~50, recent-year deltas by ~5)
# Baseline = 0 = corpus median in all variants.
#
# Reads  : outputs/fig4/novelty_percentile.parquet
# Writes : outputs/fig4/FigS4_5yr_delta.png         (five-year citations; panels of Fig. 4)
#          outputs/fig4/FigS5_annualized_delta.png  (citations per year)
#          outputs/fig4/FigS6_total_delta.png       (total citations)
import os
import sys
import matplotlib
matplotlib.use("Agg")
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from nobl import paths
from _plot import build_fig4

OUT_DIR = paths.OUTPUT_DIR / "fig4"

df = pd.read_parquet(os.path.join(OUT_DIR, "novelty_percentile.parquet"))
print(f"* loaded {len(df):,} rows")


# %% Fig. S4 — 5-yr citation delta
build_fig4(
    df, metric="delta_5yr",
    year_range=(1975, 2021), min_n=30, baseline=0,
    out_path=os.path.join(OUT_DIR, "FigS4_5yr_delta.png"),
    transparent=True,
)


# %% Fig. S6 — total-citation delta
build_fig4(
    df, metric="delta_total",
    year_range=(1975, 2021), min_n=30, baseline=0,
    out_path=os.path.join(OUT_DIR, "FigS6_total_delta.png"),
    transparent=True,
)


# %% Fig. S5 — per-year citation rate delta (age-normalized)
# rows 1&2 use tighter range (-1, 1) since L1/L2 deltas are smaller;
# row 3 keeps (-2, 2) to fit the L3 outliers (gene, protein, pathway peaks).
# legend_loc="lower left" — most trajectories rise / stay above zero here,
# so bottom-left is the clearest corner across the whole grid.
build_fig4(
    df, metric="delta_per_year",
    year_range=(1975, 2021), min_n=30, baseline=0,
    ylim={0: (-1, 1), 1: (-1, 1), 2: (-2, 2)},
    legend_loc="lower left",
    out_path=os.path.join(OUT_DIR, "FigS5_annualized_delta.png"),
    transparent=True,
)
