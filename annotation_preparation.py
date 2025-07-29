import pandas as pd
import os
from tqdm import tqdm

from functions import *


novelty_keywords = [
    "novel", 
    "innovat", 
    "first", 
    "new"
]


@timing_decorator
def conclusions_load(file_path, logger=None):
    df = pd.read_csv(file_path, sep="\t", dtype={'pmc': str, 'pmid': str})
    n = df.pmid.nunique()

    df.replace("", np.nan, inplace=True) # replace empty strings to NaN
    df.dropna(inplace=True) # drop rows that contain any NaN values
    df.drop_duplicates(subset='pmid', keep='first', inplace=True) # drop duplicated pmids

    print_or_log(logger, f'* loaded {len(df)}/{n} records with conclusions from {file_path}!')
    return df


@timing_decorator
def conclusions_combine(file_path_structured, file_path_unstructured, logger=None):
    conclusions_str = conclusions_load(file_path_structured, logger)
    conclusions_unstr = conclusions_load(file_path_unstructured, logger)
    conclusions = conclusions_str.set_index('pmid').combine_first(conclusions_unstr.set_index('pmid')).reset_index()

    print_or_log(logger, f'* combined {len(conclusions)} records with conclusions!')
    return conclusions


def contains_keywords(text, keywords):
    return any(keyword in str(text).lower() for keyword in keywords)


@timing_decorator
def novelty_detection(df, section, keywords=novelty_keywords, logger=None):
    df['novelty_mention'] = df[section].apply(lambda text: contains_keywords(text, keywords=keywords))

    n_novelty = df.pmid[df['novelty_mention'] == True].nunique()
    n = df.pmid.nunique()
    print_or_log(logger, f"* found {n_novelty}/{n} papers with self novelty mention!")
    print_or_log(logger, f"*** keyword: {keywords}, conclusion_detected_papers: {n_novelty}/{n}, estimated cost: {n_novelty/13000*20:.2f} dollars!")
    return df


@timing_decorator
def convert_to_dict(df, key_name, value_name, logger=None):
    freq = {}
    dict = {}
    for _, row in tqdm(df.iterrows(), total=len(df), desc='Processing Rows:'):
        if not pd.isna(row[key_name]):
            keys = row[key_name].split(';')
            for key in keys:
                key = key.strip()
                if key not in dict:
                    freq[key] = 1
                    dict[key] = [row[value_name]]
                else:
                    freq[key] += 1
                    dict[key].append(row[value_name])
    
    sorted_dict = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    for k, v in sorted_dict:
        print_or_log(logger, f'  {k}: {v}')

    print_or_log(logger, f"* extracted {len(dict)} keys for {len(df)} values!")
    return dict


@timing_decorator
def filter_BST(df, BST_journals, output_file_folder, logger=None, random_seed=42, sample_size=100):
    if not os.path.exists(output_file_folder):
        os.makedirs(output_file_folder)

    detected_rate = []
    for BST, journals in BST_journals.items():
        df_BST = df[df.journal.isin(journals)]
        n = len(df_BST)
        
        df_BST_detected = df_BST[df_BST['novelty_mention'] == True]
        n_detected = len(df_BST_detected)

        detected_rate.append(
            {
                "BST": BST,
                "n": n,
                "n_detected": n_detected,
                "detected_rate_str": f'{n_detected}/{n}',  # String representation
                "detected_rate_num": round(n_detected / n, 4) if n != 0 else 0  # Numerical value
            }
        )

        df_BST_detected_sampled = df_BST_detected.sample(n=min(n_detected, sample_size), random_state=random_seed)
        output_file_path = os.path.join(output_file_folder, f"{BST}.tsv")
        df_save(df_BST_detected_sampled, output_file_path, logger)
    
    print_or_log(logger, f"* saved {len(os.listdir(output_file_folder))} BST files in {output_file_folder}!")
    
    detected_rate = pd.DataFrame(detected_rate)
    parent_folder = os.path.dirname(output_file_folder)
    detected_rate_file_path = os.path.join(parent_folder, "detected_rate_pubmed.tsv")
    df_save(detected_rate, detected_rate_file_path, logger)
    
    return detected_rate


@timing_decorator
def main():
    log_fp = "your_log_fp"
    meta_fp = "your_meta_fp"
    conclusions_str_fp = "your_conclusions_str_fp"
    conclusions_unstr_fp = "your_conclusions_unstr_fp"
    journal_BSTs_fp = "your_journal_BSTs_fp"
    output_ff = "your_output_ff"
    
    logger = setup_logger(log_fp)

    # prepare data
    meta = meta_load(meta_fp, logger)
    conclusions = conclusions_combine(conclusions_str_fp, conclusions_unstr_fp, logger)
    meta_with_conclusions = pd.merge(meta, conclusions, on='pmid')
    print_or_log(logger, message=f'* found {len(meta_with_conclusions)} records with meta and conclusions!')

    # novelty detection
    print_or_log(logger, message=f"* keyword: {novelty_keywords}")
    meta_with_conclusions = novelty_detection(meta_with_conclusions, 'conclusions', keywords=novelty_keywords, logger=logger)

    # filter BST
    journal_BSTs = df_load(journal_BSTs_fp, logger)
    BST_journals = convert_to_dict(journal_BSTs, "BroadSubjectTerms", "JournalTitle", logger)
    filter_BST(meta_with_conclusions, BST_journals, output_ff, logger)


if __name__ == "__main__":
    main()