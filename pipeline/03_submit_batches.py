"""Upload request files and create Batch API jobs (requires API credentials; see .env.example).

Inputs : derived/batches/input_jsonl/split_*.jsonl
Outputs: derived/batches/batch_table.tsv (input_jsonl_fp, input_file_id, batch_id), appended
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nobl import paths
from nobl.llm import init_client
from nobl.utils import print_or_log, setup_logger


def upload_and_submit(jsonl_fp, client, logger=None):
    batch_file = client.files.create(file=open(jsonl_fp, "rb"), purpose="batch")
    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print_or_log(logger, f"* {jsonl_fp}: file {batch_file.id}, batch {batch_job.id}")
    return batch_file.id, batch_job.id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="first split index to submit")
    parser.add_argument("--end", type=int, default=None, help="last split index to submit (inclusive)")
    args = parser.parse_args()

    logger = setup_logger(paths.BATCH_DIR / "log_03_submit_batches.txt")
    client = init_client()

    jsonl_fps = sorted((paths.BATCH_DIR / "input_jsonl").glob("split_*.jsonl"))
    end = len(jsonl_fps) - 1 if args.end is None else args.end
    print_or_log(logger, f'* submitting splits {args.start}..{end} of {len(jsonl_fps)}')

    if not paths.BATCH_TABLE.exists():
        paths.BATCH_TABLE.write_text("input_jsonl_fp\tinput_file_id\tbatch_id\n")
    for jsonl_fp in jsonl_fps[args.start:end + 1]:
        file_id, batch_id = upload_and_submit(jsonl_fp, client, logger)
        with open(paths.BATCH_TABLE, 'a') as f:
            f.write(f"{jsonl_fp.name}\t{file_id}\t{batch_id}\n")


if __name__ == "__main__":
    main()
