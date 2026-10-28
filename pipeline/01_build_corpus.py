"""Build the Biomedical Novelty Claim Corpus (Analysis Set) and the article–subfield table.

Methods §1: conclusion sections (structured "Conclusion" fields first, classifier-derived
conclusions for unstructured abstracts otherwise) are joined to PubMed metadata and kept
when they contain at least one novelty keyword. Each article is linked to the Broad
Subject Terms (BSTs) of its journal; a journal may carry several BSTs.

Inputs : raw/metadata.tsv, raw/conclusions_structured.tsv, raw/conclusions_unstructured.tsv,
         raw/journal_bst.tsv
Outputs: derived/novelty_corpus.tsv, derived/article_subfields.tsv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from nobl import paths
from nobl.keywords import NOVELTY_KEYWORDS
from nobl.utils import df_load, df_save, meta_load, print_or_log, setup_logger, timing_decorator


@timing_decorator
def conclusions_load(file_path, logger=None):
    df = pd.read_csv(file_path, sep="\t", dtype={'pmc': str, 'pmid': str})
    n = df.pmid.nunique()
    df.replace("", np.nan, inplace=True)
    df.dropna(inplace=True)
    df.drop_duplicates(subset='pmid', keep='first', inplace=True)
    print_or_log(logger, f'* loaded {len(df)}/{n} records with conclusions from {file_path}!')
    return df


@timing_decorator
def conclusions_combine(file_path_structured, file_path_unstructured, logger=None):
    """Structured-abstract conclusions take precedence over classifier-derived ones."""
    conclusions_str = conclusions_load(file_path_structured, logger)
    conclusions_unstr = conclusions_load(file_path_unstructured, logger)
    conclusions = conclusions_str.set_index('pmid').combine_first(conclusions_unstr.set_index('pmid')).reset_index()
    print_or_log(logger, f'* combined {len(conclusions)} records with conclusions!')
    return conclusions


def contains_keywords(text, keywords):
    return any(keyword in str(text).lower() for keyword in keywords)


@timing_decorator
def novelty_detection(df, section, keywords=NOVELTY_KEYWORDS, logger=None):
    df['novelty_mention'] = df[section].apply(lambda text: contains_keywords(text, keywords=keywords))
    n_novelty = df.pmid[df['novelty_mention']].nunique()
    print_or_log(logger, f"* found {n_novelty}/{df.pmid.nunique()} papers with a novelty keyword in the conclusion!")
    return df


def journal_to_bsts(journal_bsts):
    """Long table JournalTitle -> BST (BroadSubjectTerms are ';'-separated)."""
    df = journal_bsts[["JournalTitle", "BroadSubjectTerms"]].dropna()
    df = df.assign(bst=df["BroadSubjectTerms"].str.split(';')).explode("bst")
    df["bst"] = df["bst"].str.strip()
    return df[["JournalTitle", "bst"]].drop_duplicates()


@timing_decorator
def main():
    paths.DERIVED.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(paths.DERIVED / "log_01_build_corpus.txt")

    meta = meta_load(paths.METADATA, logger)
    conclusions = conclusions_combine(paths.CONCLUSIONS_STRUCTURED, paths.CONCLUSIONS_UNSTRUCTURED, logger)
    meta_with_conclusions = pd.merge(meta, conclusions, on='pmid')
    print_or_log(logger, f'* found {len(meta_with_conclusions)} records with meta and conclusions!')

    print_or_log(logger, f"* keywords: {NOVELTY_KEYWORDS}")
    meta_with_conclusions = novelty_detection(meta_with_conclusions, 'conclusions', logger=logger)
    corpus = meta_with_conclusions[meta_with_conclusions['novelty_mention']].drop(columns='novelty_mention')
    df_save(corpus, paths.CORPUS, logger)

    # article -> subfield pairs
    j2b = journal_to_bsts(df_load(paths.JOURNAL_BST, logger))
    pairs = corpus[["pmid", "journal"]].merge(j2b, left_on="journal", right_on="JournalTitle")
    df_save(pairs[["pmid", "bst"]], paths.ARTICLE_SUBFIELDS, logger)


if __name__ == "__main__":
    main()
