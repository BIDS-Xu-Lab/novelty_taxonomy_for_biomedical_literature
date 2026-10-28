"""Split the Analysis Set and write one Batch API request file per split.

Inputs : derived/novelty_corpus.tsv, resources/prompt-v3.0.txt, resources/taxonomy-v3.0.txt
Outputs: derived/batches/input_tsv/split_*.tsv, derived/batches/input_jsonl/split_*.jsonl
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nobl import paths
from nobl.llm import MODEL, build_request
from nobl.utils import meta_load, print_or_log, setup_logger, timing_decorator

csv.field_size_limit(10**9)


def convert_tsv_to_jsonl(tsv_fp, jsonl_fp, taxonomy, prompt_template, model):
    with open(tsv_fp, "r", encoding="utf-8") as tsv_in, open(jsonl_fp, "w", encoding="utf-8") as jsonl_out:
        for row in csv.DictReader(tsv_in, delimiter="\t"):
            request = build_request(row["pmid"], row["conclusions"], taxonomy, prompt_template, model)
            jsonl_out.write(json.dumps(request) + "\n")


@timing_decorator
def split(df, input_tsv_dir, input_jsonl_dir, logger=None, max_length=10000):
    input_tsv_dir.mkdir(parents=True, exist_ok=True)
    input_jsonl_dir.mkdir(parents=True, exist_ok=True)

    starts = range(0, len(df), max_length)
    tsv_fps = [input_tsv_dir / f"split_{i:07d}.tsv" for i in starts]
    jsonl_fps = [input_jsonl_dir / f"split_{i:07d}.jsonl" for i in starts]
    print_or_log(logger, f'* generate {len(tsv_fps)} splits!')

    for k, fp in enumerate(tsv_fps):
        with open(fp, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=df.columns, delimiter="\t")
            writer.writeheader()
            writer.writerows(df.iloc[k * max_length:(k + 1) * max_length].to_dict(orient="records"))
    return tsv_fps, jsonl_fps


@timing_decorator
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-length", type=int, default=10000, help="requests per batch file")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    paths.BATCH_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(paths.BATCH_DIR / "log_02_prepare_batches.txt")

    prompt_template = paths.PROMPT.read_text()
    taxonomy = paths.TAXONOMY.read_text()
    print_or_log(logger, f'* model: {args.model}, prompt: {paths.PROMPT.name}, taxonomy: {paths.TAXONOMY.name}')

    df = meta_load(paths.CORPUS, logger)
    tsv_fps, jsonl_fps = split(df, paths.BATCH_DIR / "input_tsv", paths.BATCH_DIR / "input_jsonl", logger, args.max_length)
    for tsv_fp, jsonl_fp in zip(tsv_fps, jsonl_fps):
        convert_tsv_to_jsonl(tsv_fp, jsonl_fp, taxonomy, prompt_template, args.model)
    print_or_log(logger, f'*** wrote {len(jsonl_fps)} request files to {paths.BATCH_DIR / "input_jsonl"}!')


if __name__ == "__main__":
    main()
