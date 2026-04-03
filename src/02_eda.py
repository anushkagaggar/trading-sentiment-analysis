"""
02_eda.py
---------
Exploratory Data Analysis on the merged dataset.
Generates overview charts saved to assets/eda_*.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

sns.set_theme(style="darkgrid", palette="muted")
COLORS = {"Fear": "#e74c3c", "Greed": "#2ecc71", "Neutral": "#95a5a6"}


def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "merged_data.csv"), parse_dates=["Timestamp IST"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ── Plot 1: Trade volume over time coloured by sentiment ───────────────────
def plot_trade_volume_over_time(df):
    daily = df.groupby(["Date", "Sentiment"]).size().reset_index(name="Trade_Count")

    fig, ax = plt.subplots(figsize=(14, 5))
    for sentiment, grp in daily.groupby("Sentiment"):
        ax.bar(grp["Date"], grp["Trade_Count"], color=COLORS[sentiment], label=sentiment, alpha=0.85, width=1)

    ax.set_title("Daily Trade Volume by Market Sentiment", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Trades")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "eda_01_trade_volume_over_time.png"), dpi=150)
    plt.close()
    print("Saved: eda_01_trade_volume_over_time.png")


# ── Plot 2: PnL distribution by sentiment ─────────────────────────────────
def plot_pnl_distribution(df):
    closed = df[df["Closed PnL"] != 0].copy()
    closed["PnL_Clipped"] = closed["Closed PnL"].clip(-5000, 5000)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, sentiment in zip(axes, ["Fear", "Neutral", "Greed"]):
        data = closed[closed["Sentiment"] == sentiment]["PnL_Clipped"]
        ax.hist(data, bins=80, color=COLORS[sentiment], edgecolor="white", alpha=0.9)
        ax.axvline(0, color="black", linestyle="--", linewidth=1.2)
        ax.set_title(f"{sentiment}\n(n={len(data):,})", fontsize=12)
        ax.set_xlabel("Closed PnL (USD, clipped ±5K)")
        median_val = data.median()
        mean_val = data.mean()
        ax.axvline(median_val, color="navy", linestyle="-", linewidth=1.5, label=f"Median: ${median_val:.1f}")
        ax.axvline(mean_val, color="orange", linestyle="-", linewidth=1.5, label=f"Mean: ${mean_val:.1f}")
        ax.legend(fontsize=8)

    axes[0].set_ylabel("Frequency")
    fig.suptitle("Closed PnL Distribution by Sentiment", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "eda_02_pnl_distribution.png"), dpi=150)
    plt.close()
    print("Saved: eda_02_pnl_distribution.png")


# ── Plot 3: Trade direction breakdown by sentiment ─────────────────────────
def plot_direction_breakdown(df):
    top_directions = ["Open Long", "Close Long", "Open Short", "Close Short"]
    sub = df[df["Direction"].isin(top_directions)]
    breakdown = sub.groupby(["Sentiment", "Direction"]).size().unstack(fill_value=0)
    breakdown_pct = breakdown.div(breakdown.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    breakdown_pct.loc[["Fear", "Neutral", "Greed"]].plot(
        kind="bar", ax=ax, colormap="RdYlGn", edgecolor="white", width=0.6
    )
    ax.set_title("Trade Direction Mix by Market Sentiment (%)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("% of Trades")
    ax.set_xticklabels(["Fear", "Neutral", "Greed"], rotation=0)
    ax.legend(title="Direction", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "eda_03_direction_breakdown.png"), dpi=150)
    plt.close()
    print("Saved: eda_03_direction_breakdown.png")


# ── Plot 4: Top coins traded by sentiment ─────────────────────────────────
def plot_top_coins(df):
    top_coins = df["Coin"].value_counts().head(10).index
    sub = df[df["Coin"].isin(top_coins)]
    coin_sentiment = sub.groupby(["Coin", "Sentiment"]).size().unstack(fill_value=0)
    coin_sentiment = coin_sentiment.div(coin_sentiment.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(12, 6))
    coin_sentiment[["Fear", "Neutral", "Greed"]].plot(
        kind="bar", ax=ax, color=[COLORS["Fear"], COLORS["Neutral"], COLORS["Greed"]],
        edgecolor="white", width=0.7
    )
    ax.set_title("Sentiment Mix for Top 10 Traded Coins", fontsize=14, fontweight="bold")
    ax.set_ylabel("% of Trades")
    ax.set_xlabel("Coin")
    ax.legend(title="Sentiment")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "eda_04_top_coins_sentiment.png"), dpi=150)
    plt.close()
    print("Saved: eda_04_top_coins_sentiment.png")


# ── Plot 5: Average trade size by sentiment ────────────────────────────────
def plot_avg_trade_size(df):
    avg_size = df.groupby("Sentiment")["Size USD"].mean().reindex(["Fear", "Neutral", "Greed"])

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(avg_size.index, avg_size.values, color=[COLORS[s] for s in avg_size.index], edgecolor="white", width=0.5)
    for bar, val in zip(bars, avg_size.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20, f"${val:,.0f}", ha="center", fontsize=10)
    ax.set_title("Average Trade Size (USD) by Sentiment", fontsize=14, fontweight="bold")
    ax.set_ylabel("Avg Size (USD)")
    ax.set_xlabel("Sentiment")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "eda_05_avg_trade_size.png"), dpi=150)
    plt.close()
    print("Saved: eda_05_avg_trade_size.png")


# ── Summary stats table ────────────────────────────────────────────────────
def print_summary_stats(df):
    closed = df[df["Closed PnL"] != 0]
    summary = closed.groupby("Sentiment").agg(
        Total_Trades=("Closed PnL", "count"),
        Avg_PnL=("Closed PnL", "mean"),
        Median_PnL=("Closed PnL", "median"),
        Total_PnL=("Closed PnL", "sum"),
        Win_Rate=("Is_Profitable", "mean"),
        Avg_Size_USD=("Size USD", "mean"),
        Total_Fees=("Fee", "sum"),
    ).reindex(["Fear", "Neutral", "Greed"])
    summary["Win_Rate"] = (summary["Win_Rate"] * 100).round(1).astype(str) + "%"
    print("\n===== Summary Statistics by Sentiment =====")
    print(summary.to_string())


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df):,} rows\n")
    plot_trade_volume_over_time(df)
    plot_pnl_distribution(df)
    plot_direction_breakdown(df)
    plot_top_coins(df)
    plot_avg_trade_size(df)
    print_summary_stats(df)
    print("\n✅ EDA complete. Charts saved to assets/")
