"""Compare demo results with the reference copies in demo/expected/.

Usage: python demo/check_outputs.py demo/work            # check
       python demo/check_outputs.py demo/work --update   # refresh demo/expected/
"""
import shutil
import sys
from pathlib import Path

import pandas as pd

EXPECTED = Path(__file__).resolve().parent / "expected"
FILES = [
    "pipeline/derived/labels.tsv",
    "pipeline/outputs/fig1/df_taxonomy.tsv",
    "outputs/fig1/df_taxonomy.tsv",
    "outputs/fig2/top_percentage.tsv",
    "outputs/fig2/leaf_peak_years.tsv",
    "outputs/fig3/top_percentage_clustered.tsv",
    "outputs/fig3/table_S1.tsv",
    "outputs/fig3/regime_timeline.tsv",
    "outputs/fig3/transitions_overall.tsv",
]


def main():
    work = Path(sys.argv[1])
    if "--update" in sys.argv:
        for f in FILES:
            (EXPECTED / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(work / f, EXPECTED / f)
        print(f"* updated {len(FILES)} files in {EXPECTED}")
        return

    failed = 0
    for f in FILES:
        got = pd.read_csv(work / f, sep="\t")
        want = pd.read_csv(EXPECTED / f, sep="\t")
        try:
            pd.testing.assert_frame_equal(got, want, check_dtype=False, rtol=1e-6)
            print(f"  OK    {f}")
        except AssertionError as e:
            failed += 1
            print(f"  DIFF  {f}\n{e}")
    print("All demo outputs match the expected results." if not failed else f"{failed} file(s) differ.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
