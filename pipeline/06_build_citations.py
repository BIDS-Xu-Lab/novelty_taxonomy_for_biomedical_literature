"""Per-article citation counts from an iCite Database Snapshot (Methods §4).

The paper used iCite Database Snapshot 2026-03 (collection version 75,
doi:10.35092/yhjcc.4586573.v75). Download icite_metadata and open_citation_collection
from https://nih.figshare.com/collections/iCite_Database_Snapshots_NIH_Open_Citation_Collection_/4586573
and extract the CSV files into raw/icite/.

Definitions
  citations_total     iCite citation_count
  citations_per_year  citations_total / (snapshot year - publication year), rounded to 2 decimals
  citations_5yr       citations from articles published in the publication year and the
                      following four calendar years

Inputs : raw/icite/icite_metadata.csv, raw/icite/open_citation_collection.csv
Outputs: derived/citations.parquet
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb

from nobl import paths


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-year", type=int, default=2026, help="year of the iCite snapshot")
    args = parser.parse_args()

    metadata = paths.ICITE_DIR / "icite_metadata.csv"
    links = paths.ICITE_DIR / "open_citation_collection.csv"
    paths.DERIVED.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE papers AS
        SELECT CAST(pmid AS INTEGER) AS pmid, CAST(year AS SMALLINT) AS pub_year,
               CAST(COALESCE(citation_count, 0) AS INTEGER) AS citations_total
        FROM read_csv_auto('{metadata}', header = true)
        WHERE pmid IS NOT NULL AND year IS NOT NULL
    """)
    con.execute(f"""
        CREATE TABLE c5 AS
        SELECT l.referenced AS pmid, COUNT(*) AS citations_5yr
        FROM read_csv_auto('{links}', header = true) AS l
        JOIN papers AS citing ON citing.pmid = l.citing
        JOIN papers AS cited ON cited.pmid = l.referenced
        WHERE citing.pub_year BETWEEN cited.pub_year AND cited.pub_year + 4
        GROUP BY l.referenced
    """)
    con.execute(f"""
        COPY (
            SELECT p.pmid, p.pub_year,
                   CAST(COALESCE(c5.citations_5yr, 0) AS INTEGER) AS citations_5yr,
                   p.citations_total,
                   CAST(ROUND(p.citations_total / GREATEST({args.snapshot_year} - p.pub_year, 1), 2) AS FLOAT)
                       AS citations_per_year
            FROM papers AS p LEFT JOIN c5 USING (pmid)
            ORDER BY p.pmid
        ) TO '{paths.CITATIONS}' (FORMAT parquet)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{paths.CITATIONS}')").fetchone()[0]
    print(f"* saved {n:,} rows to {paths.CITATIONS}")


if __name__ == "__main__":
    main()
