# NOBL: NOvelty taxonomy for Biomedical Literature

Code for **"The changing structure of biomedical innovation"** (manuscript under review).

NOBL is a three-level taxonomy of author-claimed novelty (3 top-level categories, 31 leaf
types). This repository contains the code that builds the Biomedical Novelty Claim Corpus
from PubMed, classifies each conclusion section with GPT-4o using the frozen NOBL taxonomy
and prompt, and produces the analyses behind Figs. 1–4, Figs. S1–S6 and Table S1.

Version for peer review: `v1.0-review`.

## Contents

| Path | What it contains |
|---|---|
| `README.md` | This guide: requirements, installation, demo, usage, reproduction |
| `environment.yml` | Pinned software environment |
| `.env.example` | Template for API credentials (only needed for classification) |
| `resources/` | NOBL taxonomy (`taxonomy-v3.0.txt`) and classification prompt (`prompt-v3.0.txt`) |
| `nobl/` | Shared code: file locations, novelty keywords, taxonomy parsing, label loading, request building and parsing |
| `pipeline/` | Steps 01–06: corpus construction, GPT-4o batch classification, citation counts |
| `analysis/` | Figs. 1–4, Figs. S1–S6 and Table S1 (see the table in Section 4) |
| `demo/` | Fictional example inputs covering all 31 types, a simulated dataset generator, `run_demo.sh` and expected outputs |
| `LICENSE` | Apache License 2.0 |

## 1. System requirements

- **Operating system:** Linux or macOS. Tested on Ubuntu 24.04 LTS.
- **Language:** Python 3.11 (tested with 3.11.9).
- **Dependencies** (pinned in `environment.yml`, all tested at these versions): NumPy 1.26.4,
  pandas 2.2.2, SciPy 1.13.1, scikit-learn 1.6.1, matplotlib 3.9.1, PyArrow 17.0.0,
  openai 1.52.1 (with httpx 0.27.2), python-dotenv 1.0.1, DuckDB 1.5.2.
- **Hardware:** no special hardware. The demo needs less than 2 GB of RAM. On the full
  corpus, every analysis script ran in under 2 GB of RAM; step 01 loads all 36.5 million
  PubMed records into memory and was run on a workstation with 256 GB of RAM.
- **Non-standard resources:** classifying the full corpus (pipeline steps 03–04) requires a
  paid OpenAI or Azure OpenAI account with access to GPT-4o and the Batch API. The authors'
  estimate for the 2.37 million conclusion sections was about US$3,700 at the Batch API
  prices of 2024–2025. The demo and all analyses run without an API key.

## 2. Installation

```bash
git clone https://github.com/BIDS-Xu-Lab/novelty_taxonomy_for_biomedical_literature.git
cd novelty_taxonomy_for_biomedical_literature
conda env create -f environment.yml
conda activate nobl
```

Typical install time: about 1 minute with a warm package cache (57 s measured), and up to
about 5 minutes on a fresh machine, depending on download speed. Nothing needs to be compiled.

## 3. Demo

```bash
bash demo/run_demo.sh
```

The demo runs the complete code path on data that contain no real articles:

- **Part A — classification pipeline.** Thirty-eight fictional conclusion sections
  (`demo/examples/raw/`, written by `demo/examples/build_examples.py`) go through keyword
  filtering (step 01) and request building (step 02). Thirty-four contain a novelty keyword;
  together they cover each of the 31 NOBL types at least once, plus two "not novelty" answers
  and one response that is not valid JSON. Cached Batch API responses
  (`demo/examples/cached_responses/`) replace the API call, steps 04–05 parse them into labels,
  and the Fig. 1 script summarises the labels across the hierarchy. The cached responses were
  written by the authors to show the response format; they are not GPT-4o outputs. To classify
  the examples with GPT-4o, run steps 03–04 with an API key (see Section 4).
- **Part B — analyses.** `demo/make_demo_data.py` simulates 90,000 articles in 38 subfields
  (1975–2024) with random labels and citation counts. Every script behind Figs. 1–4 then runs
  on this dataset.

**Expected output.** The script ends with `All demo outputs match the expected results.`
It compares nine result tables with the copies in `demo/expected/`: for example, the
34 labels of Part A and their distribution over the 31 types, the leaf distribution (Fig. 1), the yearly top-level shares (Fig. 2a),
the subfield profile classes and Table S1, and the decade transitions (Fig. 3). All figures are written to
`demo/work/outputs/fig1` … `fig4`. Because the data are simulated, these numbers are not the
paper's results.

**Expected run time:** about 1 minute (50 s measured on a 6-core Intel Xeon W-2135 desktop).

## 4. Instructions for use

All scripts read inputs from `$NOBL_DATA_DIR` (default `./data`) and write figures and tables
to `$NOBL_OUTPUT_DIR` (default `./outputs`). File names are defined in `nobl/paths.py`.

### Input data (`$NOBL_DATA_DIR/raw/`)

| File | Columns | Source |
|---|---|---|
| `metadata.tsv` | `pmid`, `title`, `journal`, `year` | PubMed baseline XML parsed with pubmed_parser |
| `conclusions_structured.tsv` | `pmid`, `conclusions` | "Conclusion" field of structured abstracts |
| `conclusions_unstructured.tsv` | `pmid`, `conclusions` | conclusion sentences of unstructured abstracts, identified with the sentence classifier of Hu, Chen & Xu (*J. Healthc. Inform. Res.* 7, 542–556, 2023) |
| `journal_bst.tsv` | `JournalTitle`, `BroadSubjectTerms` (`;`-separated) | NLM Catalog Broad Subject Terms |
| `icite/icite_metadata.csv`, `icite/open_citation_collection.csv` | iCite snapshot files | NIH iCite Database Snapshots |

PubMed XML parsing and conclusion extraction happen upstream of this repository; the tables
above are their outputs.

### Pipeline

```bash
python pipeline/01_build_corpus.py        # keyword filter -> derived/novelty_corpus.tsv, derived/article_subfields.tsv
python pipeline/02_prepare_batches.py     # Batch API request files (10,000 requests each)
cp .env.example .env                      # add API credentials
python pipeline/03_submit_batches.py      # upload and start batch jobs (--start/--end select splits)
python pipeline/04_download_batches.py    # download finished jobs and parse labels
python pipeline/05_merge_labels.py        # derived/labels.tsv, derived/labels_with_year.parquet
python pipeline/06_build_citations.py     # derived/citations.parquet from an iCite snapshot
```

`04_download_batches.py` keeps the raw responses. A response whose label is not a leaf of
the taxonomy (for example, text that is not valid JSON) is counted as "not novelty" by the
analyses.

### Analyses

Run in this order (later scripts read tables written by earlier ones):

| Script | Paper | Main outputs (`$NOBL_OUTPUT_DIR/...`) |
|---|---|---|
| `analysis/fig1_taxonomy_distribution.py` | Fig. 1b | `fig1/df_taxonomy.tsv`, `fig1/sunburst.png` |
| `analysis/fig2_temporal_composition.py` | Fig. 2a–c | `fig2/top_stacked_bars.png` (2a), `fig2/leaf_stacked_bars.png` (2b), `fig2/leaf_individual_bars.png` and `fig2/leaf_peak_years.tsv` (2c) |
| `analysis/fig3/subfield_profiles.py` | Fig. S1, Table S1 | `fig3/bar.png`, `fig3/table_S1.tsv`, `fig3/top_percentage.tsv` |
| `analysis/fig3/ternary_plot.py` | Fig. S2 | `fig3/ternary.png` |
| `analysis/fig3/historical_fill_check.py` | input to Fig. 3 | `fig3/fill_shares.tsv` (claims and shares per subfield and decade) |
| `analysis/fig3/historical_dynamics.py` | Fig. 3a counts | `fig3/regime_timeline.tsv`, `fig3/transitions_overall.tsv` |
| `analysis/fig3/sankey_regime.py` | Fig. 3a | `fig3/sankey_regime.png` |
| `analysis/fig3/trajectory_overlay_all.py` | Fig. 3b | `fig3/trajectory_overlay_all.png` |
| `analysis/fig3/trajectory_snapshots_cumulative.py` | Fig. S3 | `fig3/trajectory_snapshot_cum_combined.png` |
| `analysis/fig4/01_citation_delta.py` | input to Fig. 4 and Figs. S4–S6 | `fig4/novelty_percentile.parquet` (per-article difference from the same-year corpus median) |
| `analysis/fig4/02_plot_figure4.py` | Figs. S4–S6; Fig. 4 | `fig4/FigS4_5yr_delta.png`, `fig4/FigS5_annualized_delta.png`, `fig4/FigS6_total_delta.png` |

The scripts produce the data and the plotted panels. Some published figures were then
finished by hand: layout, labels and annotations were added, and the highlighted
trajectories in Fig. 3b were marked manually. Fig. 4 shows seven of the nine Fig. S4 panels
with a hierarchy guide and peak shading added by hand, and Fig. 2c shows a selection of the
31 panels in `leaf_individual_bars.png`. Figures and tables not listed above
were not produced by code in this repository.

## 5. Reproducing the paper

1. Download the PubMed baseline (the paper used the files available on 8 January 2024) and
   build the input tables described above.
2. Run pipeline steps 01–05. The paper's run classified 2,375,414 conclusion sections
   between April and October 2025 with `temperature = 0` and the files in `resources/`.
   The model versions reported in the API responses were `gpt-4o-2024-11-20` for 2,155,412
   requests (90.7%) and `gpt-4o-2024-08-06` for 20,000 (0.8%); 200,000 (8.4%) responses
   report only `gpt-4o`. LLM outputs are not guaranteed to be identical across runs or model
   versions, so a new run can differ slightly from the paper's labels.
3. Download iCite Database Snapshot 2026-03 (collection version 75,
   doi:10.35092/yhjcc.4586573.v75) and run step 06.
4. Run the analyses in the order above.

Starting from the paper's labels and citation table, the analysis scripts reproduce the
paper's intermediate tables exactly (checked for the leaf distribution, yearly shares,
subfield profiles, subfield–decade shares, profile-class timeline, transitions and citation
differences).

## Data availability

The Biomedical Novelty Claim Corpus (2,375,414 conclusion sections with NOBL labels) will be
released at https://huggingface.co/datasets/clinicalnlplab/biomedical_novelty_claim_corpus
upon publication. PubMed, the NLM Catalog and iCite are publicly available.

## License

Apache License 2.0; see `LICENSE`.
