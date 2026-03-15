"""
SafeScreen Dataset Pipeline
============================
Run this once from the SafeScreen root folder:

    cd C:\\Users\\rucha\\SafeScreen
    python build_dataset.py

Downloads 4 Kaggle datasets, joins them, and saves:
    backend/output/master_films.csv
    backend/output/films_with_sensitivity.csv

Takes 10-20 minutes on first run (downloading ~2GB of data).
After that it's cached by kagglehub — reruns are instant.
"""

import os
import pandas as pd
import numpy as np
import kagglehub
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "backend" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("SafeScreen Dataset Pipeline")
print("=" * 60)

# ──────────────────────────────────────────────
# STEP 1 — DOWNLOAD DATASETS
# ──────────────────────────────────────────────

print("\nSTEP 1 — Downloading datasets from Kaggle...")
print("This may take 10-20 minutes on first run.\n")

try:
    path_imdb     = kagglehub.dataset_download("nhondangcode/imdb-non-commercial-datasets")
    print(f"IMDb TSVs          : {path_imdb}")
except Exception as e:
    print(f"WARNING: IMDb TSVs failed: {e}")
    path_imdb = None

try:
    path_tmdb     = kagglehub.dataset_download("asaniczka/tmdb-movies-dataset-2023-930k-movies")
    print(f"TMDB 930k          : {path_tmdb}")
except Exception as e:
    print(f"WARNING: TMDB failed: {e}")
    path_tmdb = None

try:
    path_parental = kagglehub.dataset_download("barryhaworth/imdb-parental-guide")
    print(f"IMDb Parental Guide: {path_parental}")
except Exception as e:
    print(f"WARNING: Parental guide failed: {e}")
    path_parental = None

try:
    path_movielens = kagglehub.dataset_download("grouplens/movielens-20m-dataset")
    print(f"MovieLens 20M      : {path_movielens}")
except Exception as e:
    print(f"WARNING: MovieLens failed: {e}")
    path_movielens = None


# ──────────────────────────────────────────────
# STEP 2 — LOAD IMDb CORE FILES
# ──────────────────────────────────────────────

print("\nSTEP 2 — Loading IMDb core files...")

master = pd.DataFrame()

if path_imdb:
    imdb_path = Path(path_imdb)

    # find the actual tsv.gz files — path structure varies
    def find_file(base, name):
        matches = list(Path(base).rglob(name))
        return matches[0] if matches else None

    basics_file  = find_file(imdb_path, "title.basics.tsv.gz")
    ratings_file = find_file(imdb_path, "title.ratings.tsv.gz")
    crew_file    = find_file(imdb_path, "title.crew.tsv.gz")
    names_file   = find_file(imdb_path, "name.basics.tsv.gz")

    if basics_file:
        print(f"  Loading title.basics...")
        basics = pd.read_csv(
            basics_file, sep="\t", na_values="\\N",
            dtype=str, compression="gzip", low_memory=False
        )
        basics = basics[basics["titleType"].isin(["movie", "tvSeries", "tvMovie"])]
        basics = basics[["tconst", "titleType", "primaryTitle",
                         "startYear", "runtimeMinutes", "genres"]]
        basics["startYear"]      = pd.to_numeric(basics["startYear"],      errors="coerce")
        basics["runtimeMinutes"] = pd.to_numeric(basics["runtimeMinutes"], errors="coerce")
        master = basics.copy()
        print(f"  title.basics: {len(master):,} rows")

    if ratings_file and not master.empty:
        print(f"  Loading title.ratings...")
        ratings = pd.read_csv(
            ratings_file, sep="\t", na_values="\\N", compression="gzip"
        )
        ratings.columns = ["tconst", "imdb_score", "imdb_votes"]
        master = master.merge(ratings, on="tconst", how="left")
        print(f"  After ratings join: {len(master):,} rows")

    if crew_file and names_file and not master.empty:
        print(f"  Loading crew + names...")
        crew = pd.read_csv(
            crew_file, sep="\t", na_values="\\N",
            dtype=str, compression="gzip"
        )[["tconst", "directors"]]
        crew["director_id"] = crew["directors"].str.split(",").str[0]

        names = pd.read_csv(
            names_file, sep="\t", na_values="\\N",
            dtype=str, compression="gzip",
            usecols=["nconst", "primaryName"]
        ).rename(columns={"nconst": "director_id", "primaryName": "director_name"})

        crew_named = crew.merge(names, on="director_id", how="left")
        master = master.merge(
            crew_named[["tconst", "director_name"]], on="tconst", how="left"
        )
        print(f"  After crew join: {len(master):,} rows")


# ──────────────────────────────────────────────
# STEP 3 — LOAD PARENTAL GUIDE (sensitivity backbone)
# ──────────────────────────────────────────────

print("\nSTEP 3 — Loading IMDb Parental Guide...")

SEVERITY_MAP = {"none": 1, "mild": 2, "moderate": 3, "severe": 4}

def normalise_severity(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.clip(1, 4).astype(float)
    return series.astype(str).str.strip().str.lower().map(SEVERITY_MAP)

if path_parental:
    parental_path = Path(path_parental)
    csv_files = [
        f for f in parental_path.rglob("*.csv")
        if "detail" not in f.name.lower()
    ]

    if csv_files:
        main_file = max(csv_files, key=lambda f: f.stat().st_size)
        print(f"  Using: {main_file.name}")
        parental = pd.read_csv(main_file, low_memory=False)
        print(f"  Columns: {list(parental.columns)}")

        # detect columns
        col_map = {}
        for col in parental.columns:
            lc = col.lower()
            if "sex"     in lc:                            col_map["sex"]      = col
            if "violenc" in lc:                            col_map["violence"] = col
            if "profan"  in lc:                            col_map["profanity"]= col
            if "drug"    in lc or "alcohol" in lc or lc == "drugs": col_map["drugs"] = col
            if "intens"  in lc or "frighten" in lc:       col_map["intense"]  = col

        print(f"  Sensitivity columns found: {col_map}")

        for dim, raw_col in col_map.items():
            parental[f"score_{dim}"] = normalise_severity(parental[raw_col])

        # find tconst column
        tconst_col = next(
            (c for c in parental.columns
             if "tconst" in c.lower() or c.lower() in ["id", "imdb_id"]),
            None
        )
        if tconst_col and tconst_col != "tconst":
            parental = parental.rename(columns={tconst_col: "tconst"})

        score_cols   = [f"score_{d}" for d in col_map]
        parental_clean = parental[["tconst"] + score_cols].copy()
        parental_clean["tconst"] = parental_clean["tconst"].astype(str).str.strip()

        if not master.empty:
            master["tconst"] = master["tconst"].astype(str).str.strip()
            master = master.merge(parental_clean, on="tconst", how="left")
            print(f"  After parental join: {len(master):,} rows")
            print(f"  Films with sensitivity: {master.get('score_violence', pd.Series()).notna().sum():,}")


# ──────────────────────────────────────────────
# STEP 4 — LOAD TMDB (revenue + keywords)
# ──────────────────────────────────────────────

print("\nSTEP 4 — Loading TMDB movies...")

if path_tmdb and not master.empty:
    tmdb_path  = Path(path_tmdb)
    tmdb_files = list(tmdb_path.rglob("*.csv"))

    if tmdb_files:
        tmdb_main = max(tmdb_files, key=lambda f: f.stat().st_size)
        print(f"  Using: {tmdb_main.name}")

        TMDB_COLS = ["imdb_id", "revenue", "budget", "popularity",
                     "genres", "keywords", "vote_average", "vote_count"]
        tmdb = pd.read_csv(
            tmdb_main,
            usecols=lambda c: c in TMDB_COLS,
            low_memory=False
        )
        tmdb["imdb_id"] = tmdb["imdb_id"].astype(str).str.strip()
        tmdb = tmdb[tmdb["imdb_id"].str.startswith("tt")]
        tmdb = tmdb.rename(columns={"imdb_id": "tconst"})

        master = master.merge(
            tmdb[["tconst", "revenue", "budget", "popularity"]],
            on="tconst", how="left"
        )
        print(f"  After TMDB join: {len(master):,} rows")


# ──────────────────────────────────────────────
# STEP 5 — DERIVE QUESTIONNAIRE-ALIGNED SCORES
# ──────────────────────────────────────────────

print("\nSTEP 5 — Deriving questionnaire-aligned sensitivity scores...")

# map parental guide scores → questionnaire dimension names
score_col_map = {
    "score_violence" : "q_violence",
    "score_sex"      : "q_sex",
    "score_drugs"    : "q_substances",
    "score_intense"  : "q_intense",
    "score_profanity": "q_profanity",
}
for src, dst in score_col_map.items():
    if src in master.columns:
        master[dst] = master[src]

# blood is sub-dimension of violence — use same score as baseline
if "q_violence" in master.columns:
    master["q_blood"] = master["q_violence"]

# guns, self-harm, flash — need Groq enrichment (set NaN for now)
master["q_guns"]      = np.nan
master["flag_selfharm"] = np.nan
master["flag_flash"]    = np.nan

# commercial signal — log-weighted IMDb score
if "imdb_score" in master.columns and "imdb_votes" in master.columns:
    master["commercial_score"] = (
        master["imdb_score"].fillna(0) *
        np.log1p(master["imdb_votes"].fillna(0))
    ).round(3)
else:
    master["commercial_score"] = 0.0

print(f"  q_violence filled : {master.get('q_violence', pd.Series()).notna().sum():,}")
print(f"  q_sex filled      : {master.get('q_sex',      pd.Series()).notna().sum():,}")
print(f"  q_substances filled:{master.get('q_substances',pd.Series()).notna().sum():,}")


# ──────────────────────────────────────────────
# STEP 6 — SAVE OUTPUTS
# ──────────────────────────────────────────────

print("\nSTEP 6 — Saving output files...")

if not master.empty:
    # full master
    master_path = OUTPUT_DIR / "master_films.csv"
    master.to_csv(master_path, index=False)
    print(f"  Saved: master_films.csv — {len(master):,} rows")

    # sensitivity-scored subset only
    q_cols = [c for c in master.columns if c.startswith("q_") or c.startswith("flag_")]
    scored = master[master["q_violence"].notna()].copy() if "q_violence" in master.columns else master
    scored_path = OUTPUT_DIR / "films_with_sensitivity.csv"
    scored.to_csv(scored_path, index=False)
    print(f"  Saved: films_with_sensitivity.csv — {len(scored):,} rows")

    # also copy as enriched (same file — Groq enrichment adds to this later)
    enriched_path = OUTPUT_DIR / "master_films_enriched.csv"
    master.to_csv(enriched_path, index=False)
    print(f"  Saved: master_films_enriched.csv — {len(master):,} rows")

    print(f"\nFinal schema ({len(master.columns)} columns):")
    for col in master.columns:
        null_pct = master[col].isna().mean() * 100
        print(f"  {col:<35} {str(master[col].dtype):<12} {null_pct:>5.1f}% null")
else:
    print("  WARNING: master DataFrame is empty — check dataset downloads above.")

print("\n" + "=" * 60)
print("Pipeline complete.")
print(f"Output folder: {OUTPUT_DIR}")
print("Next step: restart the FastAPI backend to load the dataset.")
print("=" * 60)