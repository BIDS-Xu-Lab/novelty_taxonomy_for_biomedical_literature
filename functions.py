import time
import logging
import os
import re
import pandas as pd
import numpy as np
import joblib
import subprocess
import concurrent.futures
import pickle


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"*** {func.__name__} took {elapsed_time/60:.4f} mins to run.")
        return result
    return wrapper


def setup_logger(log_file_path):
    log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(log_formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
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
def load_df(file_folder, file_name, logger=None):
    file_path = os.path.join(file_folder, file_name)
    df = pd.read_csv(file_path, sep='\t')
    print_or_log(logger, f'* loaded {len(df)} records from {file_path}!')
    return df


def get_file_paths(folder_path, end_pattern=".xml", logger=None):
    file_paths = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(end_pattern):
            file_path = os.path.join(folder_path, file_name)
            file_paths.append(file_path)

    print_or_log(logger, f"* found {len(file_paths)} files in {folder_path}!")
    return file_paths


@timing_decorator
def get_file_paths_dict(file_folder, end_pattern=".xml", logger=None):
    file_paths_dict = {}

    for folder_name in os.listdir(file_folder):
        folder_path = os.path.join(file_folder, folder_name)
        file_paths = get_file_paths(folder_path, end_pattern, logger)
        file_paths_dict[folder_name] = file_paths

    print_or_log(logger, f"* found {len(file_paths_dict)} folders in {file_folder}!")
    return file_paths_dict


def get_file_content(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    return content


@timing_decorator
def save_dict_to_disk(dict_obj, file_path, logger=None):
    """Save dictionary to file using pickle"""
    with open(file_path, 'wb') as f:
        pickle.dump(dict_obj, f)
        
    print_or_log(logger, f"* {len(dict_obj)} items saved to {file_path}!")
    return dict_obj


@timing_decorator
def read_dict_from_disk(file_path, logger=None):
    """Load dictionary from file using pickle"""
    with open(file_path, 'rb') as f:
        dict_obj = pickle.load(f)

    print_or_log(logger, f"* loaded {len(dict_obj)} items from {file_path}!")
    return dict_obj


@timing_decorator
def meta_load(file_path, logger=None):
    # split the file path into root and extension
    root, extension = os.path.splitext(file_path)
    
    # load df
    if extension == ".tsv":
        df = pd.read_csv(file_path, sep='\t')
    elif extension == ".npy":
        df = np.load(file_path)
    elif extension == ".joblib":
        df = joblib.load(file_path)
    
    # load df info
    print_or_log(logger, f'* loaded {len(df)} lines from {file_path}')
    
    if 'year' not in df.columns.tolist():  df = df.rename(columns={'pubdate': 'year'})
    
    # drop na
    columns_to_check = ['pmid', 'year', 'title']
    columns_to_dropna = [c for c in columns_to_check if c in df.columns]
    df = df.dropna(subset=columns_to_dropna).reset_index(drop=True)
    print_or_log(logger, f'* found {len(df)} lines after drop na in pmid, year, and title')
    
    # save storage
    # df = df[['pmid','year','journal']]
    df['pmid'] = df.pmid.astype(str)
    df['year'] = df.year.astype(int)
    
    return df