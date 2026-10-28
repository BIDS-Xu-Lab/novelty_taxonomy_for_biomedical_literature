"""Merge per-split labels into one table and attach publication year and journal.

Inputs : derived/batches/output_tsv/split_*.tsv, derived/novelty_corpus.tsv
Outputs: derived/labels.tsv (pmid, output), derived/labels_with_year.parquet (pmid, output, year, journal)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from nobl import paths
from nobl.utils import df_save, meta_load


def main():
    fps = sorted((paths.BATCH_DIR / "output_tsv").glob("split_*.tsv"))
    labels = pd.concat([pd.read_csv(fp, sep="\t", dtype={"pmid": str}) for fp in fps], ignore_index=True)
    print(f"* {len(labels)} labels from {len(fps)} files")
    df_save(labels, paths.LABELS)

    corpus = meta_load(paths.CORPUS)[["pmid", "year", "journal"]]
    with_year = labels.merge(corpus, on="pmid", how="left")
    with_year.to_parquet(paths.LABELS_WITH_YEAR, index=False)
    print(f"* saved {len(with_year)} rows to {paths.LABELS_WITH_YEAR}")


if __name__ == "__main__":
    main()
