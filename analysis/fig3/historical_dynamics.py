"""Historical-dynamics analysis for subfield × decade novelty profiles.

Uses the 3 frozen cluster centroids from the all-time subfield clustering
(same K-means as subfield_profiles.py) as fixed innovation regimes. For each
(subfield, decade) cell with N ≥ MIN_N, we standardize using the all-time
scaler and assign the profile to its nearest centroid in Euclidean distance.

Outputs (under outputs/fig3/):
- regime_timeline.tsv     — per (bst, decade): shares, N, distances, assigned regime
- transitions_overall.tsv — 3×3 transition counts pooled across all consecutive-decade pairs
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nobl import paths

OUT_DIR = paths.OUTPUT_DIR / "fig3"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FILL_SHARES = OUT_DIR / "fill_shares.tsv"
ALLTIME_TOPPCT = OUT_DIR / "top_percentage.tsv"

DECADE_ORDER = ["1980s", "1990s", "2000s", "2010s", "2020-2024"]

FEATURES_ALLTIME = ["Concept Novelty", "Finding Novelty", "Method And/Or Material Novelty"]
FEATURES_DECADE = ["Concept %", "Finding %", "Method And/Or Material %"]

FEATURE_SHORT = ["Concept", "Finding", "Method"]
REGIMES = ["Concept", "Method", "Finding"]  # ordering used in transition matrix rows/cols


def fit_alltime_regimes():
    """Same clustering as subfield_profiles.py. Returns (scaler, centroids_scaled) ordered as REGIMES."""
    df = pd.read_csv(ALLTIME_TOPPCT, sep="\t")
    df.columns = [c.strip() for c in df.columns]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[FEATURES_ALLTIME])
    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    km.fit(scaled)
    # Name each cluster id by which feature dominates its unscaled centroid.
    unscaled = scaler.inverse_transform(km.cluster_centers_)
    id_to_name = {i: FEATURE_SHORT[unscaled[i].argmax()] for i in range(3)}
    if len(set(id_to_name.values())) != 3:
        raise RuntimeError(f"Cluster naming collided: {id_to_name}")
    # Order centroids as REGIMES = [Concept, Method, Finding].
    name_to_id = {v: k for k, v in id_to_name.items()}
    centroids_scaled = np.stack([km.cluster_centers_[name_to_id[r]] for r in REGIMES])
    print(f"[all-time] scaler mean = {scaler.mean_}, scale = {scaler.scale_}")
    for r, cent in zip(REGIMES, scaler.inverse_transform(centroids_scaled)):
        print(f"  centroid {r:8s}  C={cent[0]:.2f}  F={cent[1]:.2f}  M={cent[2]:.2f}")
    return scaler, centroids_scaled


def assign_regimes(shares, scaler, centroids_scaled):
    """shares: DataFrame with FEATURES_DECADE columns (in the SAME order as FEATURES_ALLTIME).
    Returns array of nearest-regime labels and the distance matrix (n, 3)."""
    X = shares[FEATURES_DECADE].values
    X_scaled = scaler.transform(X)
    # Euclidean distance to each centroid.
    d = np.linalg.norm(X_scaled[:, None, :] - centroids_scaled[None, :, :], axis=2)
    idx = d.argmin(axis=1)
    return np.array([REGIMES[i] for i in idx]), d


def run(min_n, out_timeline, out_toverall):
    scaler, centroids_scaled = fit_alltime_regimes()

    print(f"loading {FILL_SHARES}")
    fill = pd.read_csv(FILL_SHARES, sep="\t")
    fill = fill[fill["decade"].isin(DECADE_ORDER)].copy()
    n_total = len(fill)
    fill = fill[fill["N_labeled"] >= min_n].reset_index(drop=True)
    print(f"kept {len(fill)}/{n_total} cells at N_labeled >= {min_n}")

    regimes, dists = assign_regimes(fill, scaler, centroids_scaled)
    fill["regime"] = regimes
    fill["dist_Concept"] = dists[:, 0]
    fill["dist_Method"]  = dists[:, 1]
    fill["dist_Finding"] = dists[:, 2]
    fill.to_csv(out_timeline, sep="\t", index=False)
    print(f"wrote {out_timeline}")

    # -------- Transitions between eligible adjacent decades --------
    timeline = fill.pivot(index="bst", columns="decade", values="regime").reindex(columns=DECADE_ORDER)

    overall_counts = pd.DataFrame(0, index=REGIMES, columns=REGIMES, dtype=int)
    changed = set()
    for i in range(len(DECADE_ORDER) - 1):
        d0, d1 = DECADE_ORDER[i], DECADE_ORDER[i + 1]
        pair = timeline[[d0, d1]].dropna()
        overall_counts += pd.crosstab(pair[d0], pair[d1]).reindex(index=REGIMES, columns=REGIMES, fill_value=0)
        changed |= set(pair.index[pair[d0] != pair[d1]])

    overall_long = overall_counts.stack().rename("count").reset_index()
    overall_long.columns = ["from_regime", "to_regime", "count"]
    overall_long.to_csv(out_toverall, sep="\t", index=False)
    print(f"wrote {out_toverall}")

    n_events = int(overall_counts.values.sum() - np.trace(overall_counts.values))
    print(f"{len(changed)} of {timeline.shape[0]} subfields changed class at least once, in {n_events} transition events")
    for _, r in overall_long[overall_long["from_regime"] != overall_long["to_regime"]].iterrows():
        print(f"  {r['from_regime']:>8s} → {r['to_regime']:<8s} {r['count']}")


def main():
    # subfield–decade cells with fewer than 100 mapped novelty claims are excluded (Methods §4)
    run(min_n=100,
        out_timeline=OUT_DIR / "regime_timeline.tsv",
        out_toverall=OUT_DIR / "transitions_overall.tsv")


if __name__ == "__main__":
    main()
