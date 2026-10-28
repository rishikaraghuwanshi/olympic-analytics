"""
data_loader.py
==============
Responsible for one thing only: loading and exposing the four Olympic datasets.

All four CSVs are read once at module import time. Every other module imports
`DATA` from here — no CSV path logic lives anywhere else.

Author: (your name)
"""

import os
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(
    _BASE_DIR,
    "DataSets - Global Olympic Sports Performance Analysis",
    "Cleaned Datasets",
)

_CSV_FILES = {
    "medals":     "medal_results.csv",
    "athletes":   "athletes_cleaned.csv",
    "games":      "games_summary.csv",
    "investment": "alltime_investment.csv",
}


def _load() -> dict[str, pd.DataFrame]:
    """
    Load all CSVs into DataFrames.
    Missing files produce an empty DataFrame so the app never hard-crashes.
    """
    result = {}
    for key, filename in _CSV_FILES.items():
        path = os.path.join(_DATA_DIR, filename)
        try:
            result[key] = pd.read_csv(path)
        except FileNotFoundError:
            print(f"[data_loader] WARNING: {filename} not found — using empty DataFrame.")
            result[key] = pd.DataFrame()
    return result


# ── Public API ────────────────────────────────────────────────────────────────
# Loaded once at import; all other modules use this dict.
DATA: dict[str, pd.DataFrame] = _load()


def compute_kpis() -> dict:
    """
    Return a dict of headline KPI values for the dashboard cards.

    Newly added metric vs original: `momentum_pct` — the % change in total
    medals distributed between the last two Olympic Games in the dataset.
    """
    medals_df  = DATA["medals"]
    athletes_df = DATA["athletes"]
    invest_df  = DATA["investment"]
    games_df   = DATA["games"]

    kpis: dict = {}

    # Basic counts
    kpis["total_countries"] = int(invest_df["country"].nunique())  if not invest_df.empty  else 0
    kpis["total_games"]     = int(games_df["year"].nunique())      if not games_df.empty   else 0
    kpis["total_athletes"]  = int(athletes_df["Name"].nunique())   if not athletes_df.empty else 0
    kpis["total_sports"]    = int(athletes_df["sport_category"].nunique()) if not athletes_df.empty else 0

    # Top country and most efficient
    if not invest_df.empty:
        best_row = invest_df.loc[invest_df["alltime_total_medals"].idxmax()]
        kpis["top_country"]        = best_row["country"]
        kpis["top_country_medals"] = int(best_row["alltime_total_medals"])

        eff_row = invest_df.loc[invest_df["avg_efficiency_pct"].idxmax()]
        kpis["most_efficient"]     = eff_row["country"]
        kpis["most_efficient_pct"] = round(float(eff_row["avg_efficiency_pct"]), 1)
    else:
        kpis.update({
            "top_country": "N/A", "top_country_medals": 0,
            "most_efficient": "N/A", "most_efficient_pct": 0.0,
        })

    # ── NEW: Medal Momentum ───────────────────────────────────────────────────
    # % change in TOTAL medals distributed between the last two Games years.
    kpis["momentum_pct"] = 0.0
    kpis["momentum_year"] = ""
    if not medals_df.empty:
        yearly = medals_df.groupby("year")["total_medals"].sum().sort_index()
        if len(yearly) >= 2:
            last_val  = yearly.iloc[-1]
            prev_val  = yearly.iloc[-2]
            last_year = int(yearly.index[-1])
            if prev_val > 0:
                kpis["momentum_pct"]  = round((last_val - prev_val) / prev_val * 100, 1)
                kpis["momentum_year"] = str(last_year)

    return kpis


def get_country_list() -> list[str]:
    """Return a sorted list of all country names for dropdown/search UI."""
    df = DATA["investment"]
    if df.empty:
        return []
    return sorted(df["country"].dropna().unique().tolist())


def get_olympic_years() -> list[int]:
    """Return sorted list of all Olympic years present in medal_results."""
    df = DATA["medals"]
    if df.empty:
        return []
    return sorted(df["year"].dropna().unique().tolist())
