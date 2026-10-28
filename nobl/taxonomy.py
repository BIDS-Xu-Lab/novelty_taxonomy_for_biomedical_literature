"""NOBL taxonomy parsing, label loading and category shares."""
import re
from collections import Counter

import pandas as pd

from .utils import print_or_log, timing_decorator

TOP_LEVELS = ["Concept Novelty", "Method And/Or Material Novelty", "Finding Novelty"]


def parse_file(filename):
    """
    Reads the taxonomy text file line by line and parses each line into a node:
      • 'num': the hierarchical number (e.g., "1.2.3")
      • 'heading': the category name (portion before the colon)
      • 'desc': the definition (portion after the colon), if any
      • 'children': child nodes
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    tree = []
    stack = []
    pattern = re.compile(r'^(\d+(?:\.\d+)*)(?:\s+)(.*)$')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if not match:
            continue

        numbering, text = match.group(1), match.group(2)
        heading, sep, desc = text.partition(':')
        node = {"num": numbering, "heading": heading.strip(), "desc": desc.strip() if sep else "", "children": []}

        level = numbering.count('.') + 1
        if level == 1:
            tree.append(node)
            stack = [node]
        else:
            while len(stack) >= level:
                stack.pop()
            stack[-1]["children"].append(node)
            stack.append(node)
    return tree


def read_hierarchy(filename):
    return parse_file(filename)


def get_leaf_node_names(tree):
    leaf_node_names = []
    for node in tree:
        if not node["children"]:
            leaf_node_names.append(node["heading"].lower())
        else:
            leaf_node_names.extend(get_leaf_node_names(node["children"]))
    return leaf_node_names


def get_leaf_to_top(taxonomy):
    """leaf (lower case) -> top-level heading (title case), excluding the 'Not novelty' branch."""
    leaf_to_top = {}
    for top_node in taxonomy:
        top_heading = top_node["heading"].title()
        if top_heading.lower() == "not novelty":
            continue
        stack = [top_node]
        while stack:
            n = stack.pop()
            if not n.get("children"):
                leaf_to_top[n["heading"].lower()] = top_heading
            else:
                stack.extend(n["children"])
    return leaf_to_top


@timing_decorator
def load_labels(taxonomy_fp, labels_fp, logger=None):
    """Load model labels; outputs that are not a leaf of the taxonomy are set to 'not novelty'."""
    leaf_node_names = get_leaf_node_names(read_hierarchy(taxonomy_fp))
    print_or_log(logger, f"* found {len(leaf_node_names)} leaf nodes in {taxonomy_fp}!")  # 31 + 'not novelty'

    df = pd.read_csv(labels_fp, sep="\t", dtype={'pmc': str, 'pmid': str})
    df["output"] = df["output"].str.lower().str.strip()
    print_or_log(logger, f"* loaded {len(df)} rows from {labels_fp}!")

    off_taxonomy = ~df["output"].isin(leaf_node_names)
    print_or_log(logger, f"* found {off_taxonomy.sum()} rows not in taxonomy; assigned to 'not novelty'")
    df.loc[off_taxonomy, "output"] = "not novelty"
    return df


def get_taxonomy_df(taxonomy, df_annotation):
    """Count and share (%) of each leaf; shares use all novelty claims (excluding 'not novelty') as denominator."""
    count = Counter(df_annotation["output"].str.lower())
    total_sum = sum(v for k, v in count.items() if k != 'not novelty')

    rows = []
    for top in taxonomy:
        for second in top.get("children"):
            nodes = [(second, "NA")] if not second.get("children") else []
            nodes += [(third, third.get("heading").title()) for third in second.get("children")]
            for node, third in nodes:
                count_value = count.get(node.get("heading").lower())
                rows.append({
                    "leaf": node.get("heading").title(),
                    "third": third,
                    "second": second.get("heading").title(),
                    "top": top.get("heading").title(),
                    "total": count_value,
                    "percentage": (count_value / total_sum * 100) if count_value is not None and total_sum > 0 else None,
                })
    return pd.DataFrame(rows)


def get_top_percentage(df_taxonomy, bst, top_col="top", total_col="total"):
    """Top-level shares (%) for one group (a subfield or a year)."""
    top_sums = df_taxonomy.groupby(top_col)[total_col].sum().reset_index()
    top_sums["percentage"] = (top_sums[total_col] / top_sums[total_col].sum() * 100).round(2)
    result_dict = dict(zip(top_sums[top_col], top_sums["percentage"]))
    result_dict["bst"] = bst
    return result_dict
