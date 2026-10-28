#!/usr/bin/env bash
# Run the full NOBL code path on demo data (no API key, no real data needed).
#
#   Part A  classification pipeline on 38 fictional conclusion sections covering all 31
#           NOBL types, using cached responses in place of the Batch API (steps 01, 02,
#           04 --offline, 05), then the Fig. 1 distribution of the resulting labels
#   Part B  every analysis behind Figs. 1–4 on a simulated dataset of 90,000 articles
#
# Results go to demo/work/ (deleted and recreated on each run). Usage: bash demo/run_demo.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$REPO/demo/work"
PY="${PYTHON:-python}"
export MPLBACKEND=Agg

rm -rf "$WORK"
mkdir -p "$WORK"
start=$(date +%s)

echo "=== Part A: classification pipeline on example conclusions"
export NOBL_DATA_DIR="$WORK/pipeline" NOBL_OUTPUT_DIR="$WORK/pipeline/outputs"
mkdir -p "$NOBL_DATA_DIR/derived/batches/output_jsonl"
cp -r "$REPO/demo/examples/raw" "$NOBL_DATA_DIR/raw"
"$PY" "$REPO/pipeline/01_build_corpus.py"
"$PY" "$REPO/pipeline/02_prepare_batches.py"
cp "$REPO/demo/examples/cached_responses/"*.jsonl "$NOBL_DATA_DIR/derived/batches/output_jsonl/"
"$PY" "$REPO/pipeline/04_download_batches.py" --offline
"$PY" "$REPO/pipeline/05_merge_labels.py"
"$PY" "$REPO/analysis/fig1_taxonomy_distribution.py"

echo "=== Part B: analyses on simulated data"
export NOBL_DATA_DIR="$WORK/simulated" NOBL_OUTPUT_DIR="$WORK/outputs"
"$PY" "$REPO/demo/make_demo_data.py"
for script in \
    analysis/fig1_taxonomy_distribution.py \
    analysis/fig2_temporal_composition.py \
    analysis/fig3/subfield_profiles.py \
    analysis/fig3/historical_fill_check.py \
    analysis/fig3/historical_dynamics.py \
    analysis/fig3/sankey_regime.py \
    analysis/fig3/ternary_plot.py \
    analysis/fig3/trajectory_overlay_all.py \
    analysis/fig3/trajectory_snapshots_cumulative.py \
    analysis/fig4/01_citation_delta.py \
    analysis/fig4/02_plot_figure4.py; do
    echo "--- $script"
    "$PY" "$REPO/$script" > "$WORK/log_$(basename "$script" .py).txt" 2>&1 \
        || { tail -20 "$WORK/log_$(basename "$script" .py).txt"; exit 1; }
done

echo "=== Checking results against demo/expected/"
"$PY" "$REPO/demo/check_outputs.py" "$WORK"
echo "=== Demo finished in $(( $(date +%s) - start )) s"
