"""Write the fictional example inputs and illustrative Batch API responses used by Part A of the demo.

Every sentence, title, journal, compound, gene and organism below is invented. The examples
cover each of the 31 NOBL leaf types at least once, plus "not novelty" answers and
conclusions without any novelty keyword (removed by step 01).
The responses were written by the authors to illustrate the response format; they are
not GPT-4o outputs.

Usage: python demo/examples/build_examples.py   (rewrites raw/ and cached_responses/)
"""
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from nobl.taxonomy import read_hierarchy  # noqa: E402
from nobl.keywords import NOVELTY_KEYWORDS  # noqa: E402

# (leaf or special answer, subject term(s), year, abstract type, title, conclusion)
EXAMPLES = [
    ("new attempt", "Geriatrics", 2015, "s", "Music therapy in late-stage dementia care",
     "This is the first study to explore structured music sessions in residents with late-stage dementia in rural care homes."),
    ("new perspective", "Geriatrics", 2019, "u", "Rethinking frailty as a dynamic network property",
     "These results offer a new perspective on frailty, framing it as an emergent property of interacting physiological systems."),
    ("new theory", "Psychology", 2011, "u", "A resource model of clinical decision fatigue",
     "We propose a novel theoretical framework in which decision fatigue reflects the depletion of a shared attentional resource."),
    ("new experimental method", "Dermatology", 2010, "u", "A mouse model of delayed wound closure",
     "We established a novel mouse model that reproduces the delayed wound closure seen in older adults."),
    ("new data analysis method", "Medical Informatics; Ophthalmology", 2021, "s", "Label-free retinal vessel tracing",
     "We developed a new deep learning method that traces retinal vessels without manual labels and outperforms three existing tools."),
    ("other new research method", "Education", 2017, "s", "A Delphi protocol with rolling panels",
     "We describe an original rolling-panel Delphi procedure that shortens consensus studies without losing panel diversity."),
    ("new therapy", "Cardiology", 2016, "s", "Zelvarin enhances autophagic flux in cardiomyocytes",
     "Zelvarin, a novel small molecule, restored autophagic flux and reduced infarct size, suggesting a new therapeutic strategy for ischemic heart injury."),
    ("new indicator/index/predictor", "Critical Care", 2020, "s", "The Lactate-Perfusion Index in septic shock",
     "The new Lactate-Perfusion Index predicted 28-day mortality better than either component alone in two fictional cohorts."),
    ("new tool/device", "Biomedical Engineering", 2022, "s", "Wearable sweat sensor for continuous lactate monitoring",
     "This is the first wearable sensor able to measure sweat lactate continuously during exercise for more than eight hours."),
    ("method reapplication/method combination", "Pediatrics", 2018, "s", "Adapting telemonitoring to paediatric asthma",
     "Applying an adult telemonitoring programme to children with asthma in a new setting reduced emergency visits by one quarter."),
    ("other new application method", "Health Services Research", 2014, "s", "Pharmacist-led discharge huddles",
     "We introduce an innovative pharmacist-led discharge huddle that reduced medication errors at hospital discharge."),
    ("new dataset/material", "Computational Biology", 2023, "u", "A curated atlas of single-cell profiles",
     "We provide a new curated dataset of 120,000 single-cell profiles that will serve as a resource for the community."),
    ("new substance", "Pharmacology", 2006, "u", "Isolation of quoravine from a marine sponge",
     "We isolated quoravine, a previously undescribed alkaloid, representing a novel compound class from marine sponges."),
    ("new sequence", "Virology", 1996, "u", "A complete genome of the fictional Velo virus",
     "We report for the first time the complete nucleotide sequence of the Velo virus genome."),
    ("new gene", "Genetics", 1998, "u", "Cloning of the PELT1 gene",
     "We identified and cloned PELT1, a new gene expressed predominantly in the developing kidney."),
    ("new protein", "Biochemistry", 1992, "u", "Purification of a heat-stable binding protein",
     "We purified a novel 42-kDa heat-stable protein that binds calcium with high affinity."),
    ("new genus and species", "Botany", 2009, "s", "Ardellia montana gen. et sp. nov.",
     "Ardellia montana is described as a new genus and species of flowering plant from high-altitude meadows."),
    ("new case", "Medicine", 1998, "u", "An unusual presentation of a rare vasculitis",
     "We describe an unusual case of vasculitis presenting with isolated hearing loss in an adolescent."),
    ("other new object", "Microbiology", 2013, "u", "A new phage-like particle in soil",
     "Electron microscopy revealed a new phage-like particle not previously observed in agricultural soils."),
    ("new cell property", "Cell Biology", 2008, "u", "Motile cilia on fictional epithelial cells",
     "We show for the first time that differentiated epithelial cells of this type carry motile cilia."),
    ("new candidate gene", "Genetics", 2005, "s", "Linkage scan for familial migraine",
     "Our scan points to TRIV3 as a novel candidate gene for familial migraine."),
    ("new marker", "Oncology", 2012, "s", "Serum ZK-2 in early pancreatic cancer",
     "Serum ZK-2 is a new marker that separated early pancreatic cancer from benign disease with high accuracy."),
    ("new risk variant", "Genetics", 2015, "s", "A missense variant in HOLM4 and stroke",
     "We identified a novel missense variant in HOLM4 associated with a doubled risk of early-onset stroke."),
    ("new biomedical function", "Gastroenterology", 2008, "u", "Hepatic role of the orphan receptor ORX-4",
     "We report for the first time that the orphan receptor ORX-4 regulates bile acid uptake in hepatocytes."),
    ("new target", "Pathology; Drug Therapy", 2012, "s", "KRT-9 as a candidate target in fibrosis",
     "Our findings identify KRT-9 as a new target whose inhibition attenuates fibrosis in two independent models."),
    ("other new property/feature", "Physiology", 2004, "u", "Thermal tolerance of fictional cave fish",
     "Unexpectedly, cave-dwelling fish tolerated temperatures far above those of their habitat."),
    ("new pathway", "Molecular Biology", 2002, "u", "A salvage route for nucleotide synthesis",
     "These data uncover a novel salvage pathway that supplies nucleotides when de novo synthesis is blocked."),
    ("new mechanism", "Neurology", 2017, "u", "Mitochondrial signalling links stress and sleep loss",
     "These data reveal a previously unknown mechanism by which mitochondrial signalling links chronic stress to sleep loss; we call this the new stress-sleep axis."),
    ("new association", "Epidemiology", 2019, "s", "Night-shift work and fictional thyroid disorder",
     "We found a new association between long-term night-shift work and thyroid disorder in a large fictional cohort."),
    ("other new interaction", "Ecology", 2010, "u", "Ant-fungus cooperation in leaf litter",
     "We document a surprising cooperative interaction between litter ants and a soil fungus."),
    ("other new finding", "Public Health", 2021, "s", "Water fountain use after school renovations",
     "An unprecedented rise in water fountain use followed the renovations, an effect not anticipated by the programme."),
    ("not novelty", "Health Services Research", 2018, "s", "Guideline adherence in a regional cohort",
     "New guidelines were introduced in 2015, but adherence in our cohort remained below 40% and did not change over the study period."),
    ("not novelty", "Oncology", 2007, "u", "Long-term follow-up of a screening programme",
     "Consistent with the original trial, screening reduced mortality over 20 years of follow-up."),
    (None, "General Surgery", 2014, "s", "Outcomes of laparoscopic versus open repair",
     "Laparoscopic repair was associated with shorter hospital stay; complication rates were similar between groups."),
    (None, "Pediatrics; Epidemiology", 2005, "u", "Seasonal patterns in paediatric asthma admissions",
     "Admissions peaked in early autumn, consistent with previous reports from other regions."),
    (None, "Pharmacology", 2011, "s", "Dose comparison of two common analgesics",
     "Both analgesics provided comparable pain relief at standard doses."),
    (None, "Health Services Research", 2009, "u", "Survey of clinic waiting times",
     "Median waiting time decreased after the scheduling change."),
]

REASON = "Illustrative response written by the authors for the demo (not a model output)."


def leaf_paths(tree):
    """leaf (lower case) -> 'num heading - num heading - ...' as asked for by the prompt."""
    out = {}

    def walk(node, trail):
        trail = trail + [f'{node["num"]} {node["heading"]}']
        if not node["children"]:
            out[node["heading"].lower()] = " - ".join(trail)
        for child in node["children"]:
            walk(child, trail)

    for top in tree:
        walk(top, [])
    return out


def has_keyword(text):
    return any(k in text.lower() for k in NOVELTY_KEYWORDS)


def main():
    paths_by_leaf = leaf_paths(read_hierarchy(HERE.parents[1] / "resources" / "taxonomy-v3.0.txt"))
    leaves = {k for k in paths_by_leaf if k != "not novelty"}
    covered = {e[0] for e in EXAMPLES}
    assert leaves <= covered, f"missing leaf examples: {sorted(leaves - covered)}"

    raw = HERE / "raw"
    raw.mkdir(exist_ok=True)
    meta, structured, unstructured, journals, responses = [], [], [], {}, []
    for i, (label, bsts, year, kind, title, conclusion) in enumerate(EXAMPLES, start=1):
        pmid = str(90000000 + i)
        journal = "Demo Journal of " + " and ".join(b.strip() for b in bsts.split(";"))
        journals.setdefault(journal, bsts)
        meta.append({"pmid": pmid, "title": title, "journal": journal, "year": year})
        (structured if kind == "s" else unstructured).append({"pmid": pmid, "conclusions": conclusion})

        assert has_keyword(conclusion) == (label is not None), f"keyword check failed for {pmid}: {conclusion}"
        if label is None:
            continue
        responses.append((pmid, json.dumps({"category": paths_by_leaf[label], "reason": REASON})))

    def write(name, rows, fields):
        with open(raw / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)

    write("metadata.tsv", meta, ["pmid", "title", "journal", "year"])
    write("conclusions_structured.tsv", structured, ["pmid", "conclusions"])
    write("conclusions_unstructured.tsv", unstructured, ["pmid", "conclusions"])
    write("journal_bst.tsv", [{"JournalTitle": j, "BroadSubjectTerms": b} for j, b in journals.items()],
          ["JournalTitle", "BroadSubjectTerms"])

    out = HERE / "cached_responses"
    out.mkdir(exist_ok=True)
    with open(out / "split_0000000.jsonl", "w", encoding="utf-8") as f:
        for k, (pmid, content) in enumerate(responses):
            f.write(json.dumps({
                "id": f"batch_req_demo_{k:03d}", "custom_id": pmid,
                "response": {"status_code": 200, "request_id": f"demo-{k:03d}", "body": {
                    "id": f"chatcmpl-demo-{k:03d}", "object": "chat.completion", "model": "illustrative-example",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                                 "finish_reason": "stop"}]}},
                "error": None}) + "\n")
    print(f"* {len(EXAMPLES)} examples, {len(responses)} with a novelty keyword, "
          f"{len(leaves)} leaf types covered")


if __name__ == "__main__":
    main()
