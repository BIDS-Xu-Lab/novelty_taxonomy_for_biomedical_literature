"""Generate a simulated dataset with the same schema as the paper's pipeline products.

No real articles, labels or citation counts are used. Article IDs are synthetic, labels
are drawn from made-up probabilities (Finding claims decline over time; subfields
belong to Concept-, Method- or Finding-leaning groups, and a few drift between groups),
and citation counts are random. The demo therefore checks that every analysis runs end
to end; its numbers are not the paper's results.

Outputs (under $NOBL_DATA_DIR/derived/): labels.tsv, labels_with_year.parquet,
article_subfields.tsv, citations.parquet
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from nobl import paths
from nobl.taxonomy import get_leaf_to_top, read_hierarchy

SEED = 42
YEARS = np.arange(1975, 2025)
N_PER_YEAR = np.linspace(600, 3000, len(YEARS)).astype(int)   # 90,000 articles
P_NOT_NOVELTY = 0.30
P_OFF_TAXONOMY = 0.001

# subfield -> (group, drift target or None); the drifting subfields are the ones the
# trajectory figure highlights
SUBFIELDS = {
    "Ethics": ("Concept", None), "History of Medicine": ("Concept", None), "Psychology": ("Concept", None),
    "Nursing": ("Concept", None), "Public Health": ("Concept", None), "Education": ("Concept", None),
    "Social Sciences": ("Concept", None), "Epidemiology": ("Concept", None), "Health Services": ("Concept", None),
    "Medical Informatics": ("Method", None), "Radiotherapy": ("Method", None), "Biomedical Engineering": ("Method", None),
    "Diagnostic Imaging": ("Method", None), "Computational Biology": ("Method", None), "Radiology": ("Method", None),
    "General Surgery": ("Method", None), "Therapeutics": ("Method", None), "Nanotechnology": ("Method", None),
    "Bacteriology": ("Finding", None), "Pathology": ("Finding", None), "Virology": ("Finding", None),
    "Molecular Biology": ("Finding", None), "Neurology": ("Finding", None), "Allergy and Immunology": ("Finding", None),
    "Genetics": ("Finding", None), "Biochemistry": ("Finding", None), "Cardiology": ("Finding", None),
    "Endocrinology": ("Finding", None), "Gastroenterology": ("Finding", None), "Hematology": ("Finding", None),
    "Behavioral Sciences": ("Finding", "Concept"), "Environmental Health": ("Finding", "Concept"),
    "Biotechnology": ("Finding", "Method"), "Chemistry": ("Finding", "Method"), "Drug Therapy": ("Finding", "Method"),
    "Ophthalmology": ("Finding", "Method"), "Orthopedics": ("Finding", "Method"), "Urology": ("Finding", "Method"),
}
GROUP_PROFILE = {  # Concept, Method And/Or Material, Finding
    "Concept": np.array([0.45, 0.25, 0.30]),
    "Method": np.array([0.12, 0.58, 0.30]),
    "Finding": np.array([0.10, 0.22, 0.68]),
}
TOPS = ["Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"]
CITATION_MEAN = {"Concept Novelty": 9.0, "Method And/Or Material Novelty": 7.5, "Finding Novelty": 8.5}


def top_probs(group, drift, year):
    t = (year - YEARS[0]) / (YEARS[-1] - YEARS[0])
    p = GROUP_PROFILE[group].copy()
    if drift is not None:
        p = (1 - t) * p + t * GROUP_PROFILE[drift]
    p = p + t * np.array([0.04, 0.06, -0.10])  # corpus-wide shift away from Finding
    p = np.clip(p, 0.02, None)
    return p / p.sum()


def main():
    rng = np.random.default_rng(SEED)
    taxonomy = read_hierarchy(paths.TAXONOMY)
    leaf_to_top = get_leaf_to_top(taxonomy)
    leaves_by_top = {top: [leaf for leaf, t in leaf_to_top.items() if t == top] for top in TOPS}
    leaf_weights = {top: rng.dirichlet(np.ones(len(leaves)) * 2) for top, leaves in leaves_by_top.items()}

    names = list(SUBFIELDS)
    rows, pairs = [], []
    pmid = 10_000_000
    for year, n in zip(YEARS, N_PER_YEAR):
        for _ in range(n):
            pmid += 1
            main_bst = names[rng.integers(len(names))]
            bsts = [main_bst]
            if rng.random() < 0.3:  # about a third of journals carry a second subject term
                bsts.append(names[rng.integers(len(names))])
            group, drift = SUBFIELDS[main_bst]

            u = rng.random()
            if u < P_OFF_TAXONOMY:
                output, top = "none json", None
            elif u < P_NOT_NOVELTY:
                output, top = "not novelty", None
            else:
                top = TOPS[rng.choice(3, p=top_probs(group, drift, year))]
                output = rng.choice(leaves_by_top[top], p=leaf_weights[top])

            mean = CITATION_MEAN.get(top, 6.0) * (1.3 if year < 2000 else 1.0)
            c5 = int(rng.negative_binomial(2, 2 / (2 + mean)))
            total = c5 + int(rng.negative_binomial(2, 2 / (2 + mean * (2024 - year) / 10)))
            rows.append((pmid, output, int(year), f"Demo Journal of {main_bst}", c5, total))
            pairs.extend((pmid, b) for b in dict.fromkeys(bsts))

    df = pd.DataFrame(rows, columns=["pmid", "output", "year", "journal", "citations_5yr", "citations_total"])
    paths.DERIVED.mkdir(parents=True, exist_ok=True)

    df[["pmid", "output"]].to_csv(paths.LABELS, sep="\t", index=False)
    lw = df[["pmid", "output", "year", "journal"]].copy()
    lw["pmid"] = lw["pmid"].astype(str)
    lw.to_parquet(paths.LABELS_WITH_YEAR, index=False)
    pd.DataFrame(pairs, columns=["pmid", "bst"]).to_csv(paths.ARTICLE_SUBFIELDS, sep="\t", index=False)

    cit = pd.DataFrame({
        "pmid": df.pmid.astype("int32"),
        "pub_year": df.year.astype("int16"),
        "citations_5yr": df.citations_5yr.astype("int32"),
        "citations_total": df.citations_total.astype("int32"),
        "citations_per_year": (df.citations_total / (2026 - df.year)).round(2).astype("float32"),
    })
    cit.to_parquet(paths.CITATIONS, index=False)
    print(f"* simulated {len(df):,} articles, {len(pairs):,} article–subfield pairs in {paths.DERIVED}")


if __name__ == "__main__":
    main()
