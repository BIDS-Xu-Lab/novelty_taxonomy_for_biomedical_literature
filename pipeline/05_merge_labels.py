"""Merge per-split labels into one table and attach publication year and journal.

Every article in the corpus must have exactly one label, and every label must be a leaf of
the taxonomy (including "not novelty"). Otherwise nothing is written: the articles without
a label (for example from a batch that was not completed) or with an invalid label are
listed in derived/batches/to_resubmit.tsv, to be classified again.

Inputs : derived/batches/output_tsv/split_*.tsv, derived/novelty_corpus.tsv
Outputs: derived/labels.tsv (pmid, output), derived/labels_with_year.parquet (pmid, output, year, journal)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from nobl import paths
from nobl.taxonomy import get_leaf_node_names, read_hierarchy
from nobl.utils import df_save, meta_load


def main():
    fps = sorted((paths.BATCH_DIR / "output_tsv").glob("split_*.tsv"))
    labels = pd.concat([pd.read_csv(fp, sep="\t", dtype={"pmid": str}) for fp in fps], ignore_index=True)
    labels["output"] = labels["output"].str.lower().str.strip()
    print(f"* {len(labels)} labels from {len(fps)} files")

    corpus = meta_load(paths.CORPUS)[["pmid", "year", "journal"]]
    leaves = set(get_leaf_node_names(read_hierarchy(paths.TAXONOMY)))
    missing = sorted(set(corpus["pmid"]) - set(labels["pmid"]))
    duplicated = sorted(set(labels.loc[labels["pmid"].duplicated(), "pmid"]))
    invalid = sorted(set(labels.loc[~labels["output"].isin(leaves), "pmid"]))
    problems = (
        [(p, "no label") for p in missing]
        + [(p, "more than one label") for p in duplicated]
        + [(p, "label not in taxonomy") for p in invalid]
    )
    if problems:
        fp = paths.BATCH_DIR / "to_resubmit.tsv"
        pd.DataFrame(problems, columns=["pmid", "problem"]).to_csv(fp, sep="\t", index=False)
        sys.exit(f"* {len(missing)} articles without a label, {len(duplicated)} with more than one, "
                 f"{len(invalid)} with a label not in the taxonomy; listed in {fp}")

    df_save(labels, paths.LABELS)
    with_year = labels.merge(corpus, on="pmid", how="left")
    with_year.to_parquet(paths.LABELS_WITH_YEAR, index=False)
    print(f"* every article has one valid label; saved {len(with_year)} rows to {paths.LABELS_WITH_YEAR}")


if __name__ == "__main__":
    main()
