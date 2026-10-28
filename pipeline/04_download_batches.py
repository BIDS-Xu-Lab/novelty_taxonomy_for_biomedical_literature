"""Download finished Batch API jobs and extract one label per article.

Inputs : derived/batches/batch_table.tsv
Outputs: derived/batches/output_jsonl/split_*.jsonl (raw responses),
         derived/batches/output_tsv/split_*.tsv (pmid, output)

With --offline, skips the API and only converts existing output_jsonl files; the demo uses
this with the cached responses in demo/.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from nobl import paths
from nobl.llm import init_client, parse_batch_output_line
from nobl.utils import print_or_log, setup_logger


def convert_jsonl_to_tsv(jsonl_fp, tsv_fp):
    with open(jsonl_fp, "r", encoding="utf-8") as json_in, open(tsv_fp, "w", encoding="utf-8") as tsv_out:
        tsv_out.write("pmid\toutput\n")
        for line in json_in:
            if line.strip():
                pmid, label = parse_batch_output_line(line)
                tsv_out.write(f"{pmid}\t{label}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="convert existing output_jsonl files only")
    args = parser.parse_args()

    out_jsonl_dir = paths.BATCH_DIR / "output_jsonl"
    out_tsv_dir = paths.BATCH_DIR / "output_tsv"
    out_jsonl_dir.mkdir(parents=True, exist_ok=True)
    out_tsv_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(paths.BATCH_DIR / "log_04_download_batches.txt")

    if not args.offline:
        client = init_client()
        table = pd.read_csv(paths.BATCH_TABLE, sep="\t")
        for name, batch_id in zip(table.input_jsonl_fp, table.batch_id):
            batch = client.batches.retrieve(batch_id)
            if batch.status != "completed":
                print_or_log(logger, f"* {batch_id} is {batch.status}; skipped (step 05 lists its articles)")
                continue
            (out_jsonl_dir / Path(name).name).write_text(client.files.content(batch.output_file_id).text)
            print_or_log(logger, f"* downloaded {batch_id}")

    for jsonl_fp in sorted(out_jsonl_dir.glob("split_*.jsonl")):
        tsv_fp = out_tsv_dir / f"{jsonl_fp.stem}.tsv"
        convert_jsonl_to_tsv(jsonl_fp, tsv_fp)
        print_or_log(logger, f"* converted {jsonl_fp.name} -> {tsv_fp}")


if __name__ == "__main__":
    main()
