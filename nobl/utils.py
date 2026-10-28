import time
import logging

import pandas as pd


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"*** {func.__name__} took {(time.time() - start_time) / 60:.4f} mins to run.")
        return result
    return wrapper


def setup_logger(log_file_path=None):
    log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger("nobl")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    if log_file_path:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger


def print_or_log(logger, message):
    if logger:
        logger.info(message)
    else:
        print(message)


@timing_decorator
def df_load(file_path, logger=None):
    df = pd.read_csv(file_path, sep="\t", dtype={'pmc': str, 'pmid': str})
    print_or_log(logger, f"* loaded {len(df)} rows from {file_path}!")
    return df


@timing_decorator
def df_save(df, file_path, logger=None):
    df.to_csv(file_path, sep="\t", index=False)
    print_or_log(logger, f"* saved {len(df)} rows to {file_path}!")
    return df


@timing_decorator
def meta_load(file_path, logger=None):
    df = pd.read_csv(file_path, sep='\t')
    print_or_log(logger, f'* loaded {len(df)} lines from {file_path}')

    if 'year' not in df.columns.tolist():
        df = df.rename(columns={'pubdate': 'year'})

    columns_to_dropna = [c for c in ['pmid', 'year', 'title'] if c in df.columns]
    df = df.dropna(subset=columns_to_dropna).reset_index(drop=True)
    print_or_log(logger, f'* found {len(df)} lines after drop na in pmid, year, and title')

    df['pmid'] = df.pmid.astype(str)
    df['year'] = df.year.astype(int)
    return df
