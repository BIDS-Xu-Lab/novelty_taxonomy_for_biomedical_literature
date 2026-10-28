"""Distribution of novelty claims across the NOBL hierarchy (Fig. 1b).

Shares use all mapped novelty claims as the denominator ('not novelty' and off-taxonomy
outputs are excluded).

Inputs : derived/labels.tsv
Outputs: outputs/fig1/df_taxonomy.tsv (count and share of every leaf), top_level_shares.tsv,
         sunburst.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from nobl import paths
from nobl.taxonomy import get_taxonomy_df, get_top_percentage, load_labels, read_hierarchy


def get_colors(colormap_name, n_colors, c_range=(0.2, 0.8)):
    cmap = plt.get_cmap(colormap_name)
    return [cmap(v) for v in np.linspace(c_range[0], c_range[1], n_colors)]


def sunburst(df, fp, second_label=0, third_label=0):
    fig, ax = plt.subplots(figsize=(7, 7))
    startangle = 30

    # inner ring: top-level categories
    vals_1 = df.groupby(by='top')['percentage'].sum().reset_index()['percentage']
    clrs_1 = [get_colors('Reds', 3, (0.3, 1))[0], get_colors('Blues', 3, (0.3, 1))[0], get_colors('YlGn', 3, (0.3, 1))[0]]
    ax.pie(vals_1, radius=0.5, colors=clrs_1, startangle=startangle, wedgeprops=dict(width=0.3, edgecolor='w'))

    # middle ring: level-2 categories
    tmp = df.groupby(by=['top', 'second'])['percentage'].sum().reset_index()

    def get_label(r):
        if r['percentage'] > second_label:
            return r['second'].replace(' ', '\n').replace('/', '\n') + "\n{:,.2f}%".format(r['percentage'])
        return ''

    clrs_2 = get_colors('Reds', 3, (0.5, 0.7)) + get_colors('Blues', 4, (0.2, 0.5)) + get_colors('YlGn', 3, (0.5, 0.6))
    ax.pie(tmp['percentage'], radius=0.75, labels=tmp.apply(get_label, axis=1), labeldistance=0.8, colors=clrs_2,
           startangle=startangle, textprops=dict(color="#333333", ha='center'), wedgeprops=dict(width=0.3, edgecolor='w'))

    # outer ring: level-3 categories (level-2 leaves are drawn invisible)
    tmp = df.groupby(by=['top', 'second', 'third'])['percentage'].sum().reset_index()
    invisible_idxes = tmp[tmp.third == 'NA'].index
    clrs_3 = get_colors('Reds', 3, (0.6, 0.8)) + get_colors('Blues', 19, (0.2, 0.5)) + get_colors('YlGn', 9, (0.5, 0.6))
    wedges, _ = ax.pie(tmp['percentage'], radius=1.1, colors=clrs_3, startangle=startangle,
                       wedgeprops=dict(width=0.25, edgecolor='w'))
    for i in invisible_idxes:
        if i < len(wedges):
            wedges[i].set_alpha(0)

    kw = dict(arrowprops=dict(arrowstyle="-", ec='#cccccc'),
              bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="w", lw=0.1), zorder=0, va="center")
    for i, p in enumerate(wedges):
        if tmp.loc[i]['percentage'] < third_label or tmp.loc[i]['third'] == 'NA':
            continue
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        y, x = np.sin(np.deg2rad(ang)), np.cos(np.deg2rad(ang))
        kw["arrowprops"].update({"connectionstyle": f"angle,angleA=0,angleB={ang}"})
        ax.annotate(f"{tmp.loc[i]['third']} ({tmp.loc[i]['percentage']:.2f}%)", xy=(x, y),
                    xytext=(1.35 * np.sign(x), 1.4 * y), horizontalalignment={-1: "right", 1: "left"}[int(np.sign(x))], **kw)

    fig.savefig(fp, dpi=300, bbox_inches='tight')
    plt.close(fig)


def main():
    taxonomy = read_hierarchy(paths.TAXONOMY)
    df_annotation = load_labels(paths.TAXONOMY, paths.LABELS)

    df_taxonomy = get_taxonomy_df(taxonomy, df_annotation)
    df_taxonomy.to_csv(paths.out("fig1", "df_taxonomy.tsv"), sep="\t", index=False)

    n_claims = int(df_taxonomy.total.fillna(0).sum())
    top = get_top_percentage(df_taxonomy, bst="all")
    top.pop("bst")
    pd.DataFrame({"top": list(top), "percentage": list(top.values())}).to_csv(
        paths.out("fig1", "top_level_shares.tsv"), sep="\t", index=False)
    print(f"* {n_claims} mapped novelty claims of {len(df_annotation)} classified conclusions")
    print(f"* top-level shares (%): {top}")

    sunburst(df_taxonomy, paths.out("fig1", "sunburst.png"), second_label=3, third_label=0.5)


if __name__ == "__main__":
    main()
