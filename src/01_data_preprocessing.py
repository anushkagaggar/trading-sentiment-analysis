"""
01_data_preprocessing.py
------------------------
Loads, cleans, and merges the two datasets.
Output: data/merged_data.csv  (used by all subsequent scripts)
"""

import pandas as pd
import numpy as np
import os

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TRADER_FILE = os.path.join(DATA_DIR, "historical_data.xlsx")
FG_FILE = os.path.join(DATA_DIR, "fear_greed_index.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "merged_data.csv")


# ── Load trader data ───────────────────────────────────────────────────────
def load_trader_data(path):
    df = pd.read_excel(path)

    # Normalise column names
    df.columns = [c.strip() for c in df.columns]

    # Parse timestamps
    df["Timestamp IST"] = pd.to_datetime(df["Timestamp IST"], errors="coerce")
    df["Date"] = df["Timestamp IST"].dt.date

    # Drop rows with no valid timestamp
    df = df.dropna(subset=["Timestamp IST"])

    # Ensure numeric types
    for col in ["Execution Price", "Size Tokens", "Size USD", "Closed PnL", "Fee"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derive useful flags
    df["Is_Profitable"] = df["Closed PnL"] > 0

    # Standardise direction labels
    df["Direction"] = df["Direction"].str.strip()

    print(f"Trader data loaded: {len(df):,} rows, {df['Account'].nunique()} accounts")
    print(f"Date range: {df['Timestamp IST'].min().date()} → {df['Timestamp IST'].max().date()}")
    return df


# ── Load Fear & Greed data ─────────────────────────────────────────────────
def load_fg_data(path):
    """
    Expected columns: date (YYYY-MM-DD), classification (Fear / Greed / Neutral)
    The raw CSV from alternative.me typically has: date, value, classification
    We also create a numeric Fear_Score where Fear=1, Neutral=2, Greed=3
    """
    fg = pd.read_csv(path)
    fg.columns = [c.strip().lower() for c in fg.columns]

    # Flexible date parsing
    date_col = next((c for c in fg.columns if "date" in c), None)
    class_col = next((c for c in fg.columns if "class" in c), None)

    if date_col is None or class_col is None:
        raise ValueError(f"Expected 'date' and 'classification' columns. Found: {fg.columns.tolist()}")

    fg = fg.rename(columns={date_col: "Date", class_col: "Sentiment"})
    fg["Date"] = pd.to_datetime(fg["Date"], errors="coerce").dt.date

    # Simplify to Fear / Greed / Neutral
    def simplify_sentiment(s):
        s = str(s).lower()
        if "extreme fear" in s or s == "fear":
            return "Fear"
        elif "extreme greed" in s or s == "greed":
            return "Greed"
        else:
            return "Neutral"

    fg["Sentiment"] = fg["Sentiment"].apply(simplify_sentiment)

    # Keep original classification too if value column exists
    if "value" in fg.columns:
        fg["FG_Value"] = pd.to_numeric(fg["value"], errors="coerce")
        fg["Sentiment_Detail"] = pd.cut(
            fg["FG_Value"],
            bins=[0, 25, 45, 55, 75, 100],
            labels=["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"],
        )

    fg = fg.dropna(subset=["Date"])
    print(f"Fear & Greed data loaded: {len(fg):,} rows")
    print(fg["Sentiment"].value_counts().to_string())
    return fg


# ── Merge ──────────────────────────────────────────────────────────────────
def merge_datasets(trader_df, fg_df):
    merged = trader_df.merge(fg_df[["Date", "Sentiment"] + (["FG_Value", "Sentiment_Detail"] if "FG_Value" in fg_df.columns else [])],
                             on="Date", how="left")

    missing = merged["Sentiment"].isna().sum()
    pct_missing = 100 * missing / len(merged)
    print(f"\nMerge complete: {len(merged):,} rows")
    print(f"Rows without sentiment match: {missing:,} ({pct_missing:.1f}%)")

    # Drop rows with no sentiment (outside FG index date range)
    merged = merged.dropna(subset=["Sentiment"])
    print(f"Final merged dataset: {len(merged):,} rows")
    return merged


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    trader_df = load_trader_data(TRADER_FILE)
    fg_df = load_fg_data(FG_FILE)
    merged = merge_datasets(trader_df, fg_df)

    merged.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Merged data saved to: {OUTPUT_FILE}")
    print("\nColumn list:")
    print(merged.columns.tolist())
    print("\nSample rows:")
    print(merged.head(3).to_string())
