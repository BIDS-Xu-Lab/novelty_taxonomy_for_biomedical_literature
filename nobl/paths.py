"""File locations shared by every pipeline and analysis script.

Two environment variables control where data are read from and written to:

    NOBL_DATA_DIR    inputs and pipeline products (default: <repo>/data)
    NOBL_OUTPUT_DIR  figures and analysis tables  (default: <repo>/outputs)

demo/run_demo.sh points both at demo/ so the demo never touches real data.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESOURCES = REPO / "resources"

DATA_DIR = Path(os.environ.get("NOBL_DATA_DIR", REPO / "data"))
OUTPUT_DIR = Path(os.environ.get("NOBL_OUTPUT_DIR", REPO / "outputs"))

# frozen classification protocol (Methods §2)
TAXONOMY = RESOURCES / "taxonomy-v3.0.txt"
PROMPT = RESOURCES / "prompt-v3.0.txt"

# raw inputs (see README, "Input data")
RAW = DATA_DIR / "raw"
METADATA = RAW / "metadata.tsv"                       # pmid, title, journal, year
CONCLUSIONS_STRUCTURED = RAW / "conclusions_structured.tsv"      # pmid, conclusions
CONCLUSIONS_UNSTRUCTURED = RAW / "conclusions_unstructured.tsv"  # pmid, conclusions
JOURNAL_BST = RAW / "journal_bst.tsv"                 # JournalTitle, BroadSubjectTerms
ICITE_DIR = RAW / "icite"                             # iCite snapshot (icite_metadata + open_citation_collection)

# pipeline products
DERIVED = DATA_DIR / "derived"
CORPUS = DERIVED / "novelty_corpus.tsv"               # keyword-filtered conclusions (Analysis Set)
ARTICLE_SUBFIELDS = DERIVED / "article_subfields.tsv"  # pmid, bst (one row per article–subfield pair)
BATCH_DIR = DERIVED / "batches"                       # input_tsv/, input_jsonl/, output_jsonl/, output_tsv/
BATCH_TABLE = BATCH_DIR / "batch_table.tsv"           # input_jsonl_fp -> batch_id
LABELS = DERIVED / "labels.tsv"                       # pmid, output (raw model label)
LABELS_WITH_YEAR = DERIVED / "labels_with_year.parquet"  # pmid, output, year, journal
CITATIONS = DERIVED / "citations.parquet"             # pmid, pub_year, citations_5yr, citations_total, citations_per_year


def out(*parts):
    """Return OUTPUT_DIR/<parts>, creating the parent folder."""
    p = OUTPUT_DIR.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
