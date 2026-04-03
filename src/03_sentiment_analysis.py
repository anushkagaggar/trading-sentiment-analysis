"""
03_sentiment_analysis.py
------------------------
Deep dive: Sentiment vs Trader Performance
Charts saved to assets/sentiment_*.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
COLORS = {"Fear": "#e74c3c", "Greed": "#2ecc71", "Neutral": "#95a5a6"}
SENTIMENT_ORDER = ["Fear", "Neutral", "Greed"]


def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "merged_data.csv"), parse_dates=["Timestamp IST", "Date"])
    df["Is_Profitable"] = df["Closed PnL"] > 0
    return df


# ── Plot 1: Win rate by sentiment ──────────────────────────────────────────
def plot_win_rate(df):
    closed = df[df["Closed PnL"] != 0]
    win_rates = closed.groupby("Sentiment")["Is_Profitable"].mean().reindex(SENTIMENT_ORDER) * 100

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(win_rates.index, win_rates.values, color=[COLORS[s] for s in win_rates.index], width=0.5, edgecolor="white")
    ax.axhline(50, color="black", linestyle="--", linewidth=1, label="50% breakeven")
    for bar, val in zip(bars, win_rates.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{val:.1f}%", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 80)
    ax.set_title("Win Rate (% Profitable Trades) by Sentiment", fontsize=13, fontweight="bold")
    ax.set_ylabel("Win Rate (%)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "sentiment_01_win_rate.png"), dpi=150)
    plt.close()
    print("Saved: sentiment_01_win_rate.png")


# ── Plot 2: Cumulative PnL over time by sentiment phase ───────────────────
def plot_cumulative_pnl_by_sentiment(df):
    """
    Shows cumulative PnL of all traders split into Fear / Neutral / Greed phases
    """
    closed = df[df["Closed PnL"] != 0].sort_values("Timestamp IST")

    fig, ax = plt.subplots(figsize=(14, 6))
    for sentiment in SENTIMENT_ORDER:
        sub = closed[closed["Sentiment"] == sentiment].sort_values("Timestamp IST")
        cum_pnl = sub["Closed PnL"].cumsum().reset_index(drop=True)
        ax.plot(cum_pnl.index, cum_pnl.values, color=COLORS[sentiment], label=sentiment, linewidth=1.5)

    ax.set_title("Cumulative PnL During Each Sentiment Phase", fontsize=13, fontweight="bold")
    ax.set_xlabel("Trade Sequence (within each phase)")
    ax.set_ylabel("Cumulative PnL (USD)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "sentiment_02_cumulative_pnl.png"), dpi=150)
    plt.close()
    print("Saved: sentiment_02_cumulative_pnl.png")


# ── Plot 3: Open Long/Short ratio by sentiment ────────────────────────────
def plot_long_short_ratio(df):
    opens = df[df["Direction"].isin(["Open Long", "Open Short"])]
    ratio = opens.groupby(["Sentiment", "Direction"]).size().unstack(fill_value=0)
    ratio["Long_Short_Ratio"] = ratio["Open Long"] / ratio["Open Short"].replace(0, np.nan)
    ratio = ratio.reindex(SENTIMENT_ORDER)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(ratio.index, ratio["Long_Short_Ratio"], color=[COLORS[s] for s in ratio.index], width=0.5, edgecolor="white")
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.2, label="1:1 ratio")
    for bar, val in zip(bars, ratio["Long_Short_Ratio"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01, f"{val:.2f}x", ha="center", fontsize=11)
    ax.set_title("Long/Short Open Ratio by Sentiment", fontsize=13, fontweight="bold")
    ax.set_ylabel("Open Long : Open Short ratio")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "sentiment_03_long_short_ratio.png"), dpi=150)
    plt.close()
    print("Saved: sentiment_03_long_short_ratio.png")


# ── Plot 4: Boxplot — PnL per trade by sentiment ──────────────────────────
def plot_pnl_boxplot(df):
    closed = df[(df["Closed PnL"] != 0) & (df["Closed PnL"].between(-3000, 3000))].copy()
    closed["Sentiment"] = pd.Categorical(closed["Sentiment"], categories=SENTIMENT_ORDER, ordered=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    sns.boxplot(data=closed, x="Sentiment", y="Closed PnL", palette=COLORS, ax=ax,
                order=SENTIMENT_ORDER, fliersize=2, linewidth=1.2)
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("PnL per Trade Distribution by Sentiment (clipped ±$3K)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Closed PnL (USD)")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "sentiment_04_pnl_boxplot.png"), dpi=150)
    plt.close()
    print("Saved: sentiment_04_pnl_boxplot.png")


# ── Plot 5: Heatmap — Avg PnL by coin × sentiment ────────────────────────
def plot_coin_sentiment_heatmap(df):
    top_coins = df["Coin"].value_counts().head(15).index
    closed = df[(df["Closed PnL"] != 0) & (df["Coin"].isin(top_coins))]
    pivot = closed.groupby(["Coin", "Sentiment"])["Closed PnL"].mean().unstack(fill_value=0)
    pivot = pivot.reindex(columns=SENTIMENT_ORDER)

    fig, ax = plt.subplots(figsize=(8, 8))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="RdYlGn", center=0, ax=ax,
                linewidths=0.5, linecolor="white", cbar_kws={"label": "Avg PnL (USD)"})
    ax.set_title("Avg PnL per Trade: Coin × Sentiment", fontsize=13, fontweight="bold")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Coin")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "sentiment_05_coin_heatmap.png"), dpi=150)
    plt.close()
    print("Saved: sentiment_05_coin_heatmap.png")


# ── Statistical significance tests ────────────────────────────────────────
def run_significance_tests(df):
    closed = df[df["Closed PnL"] != 0]
    fear_pnl = closed[closed["Sentiment"] == "Fear"]["Closed PnL"].dropna()
    greed_pnl = closed[closed["Sentiment"] == "Greed"]["Closed PnL"].dropna()
    neutral_pnl = closed[closed["Sentiment"] == "Neutral"]["Closed PnL"].dropna()

    t_stat, p_val = stats.ttest_ind(fear_pnl, greed_pnl, equal_var=False)
    print("\n===== Statistical Tests =====")
    print(f"Welch's t-test: Fear PnL vs Greed PnL")
    print(f"  t-statistic : {t_stat:.4f}")
    print(f"  p-value     : {p_val:.4f}")
    print(f"  Significant : {'YES ✓' if p_val < 0.05 else 'NO ✗'} (α=0.05)")

    f_stat, p_anova = stats.f_oneway(fear_pnl, neutral_pnl, greed_pnl)
    print(f"\nOne-way ANOVA across all three sentiment groups:")
    print(f"  F-statistic : {f_stat:.4f}")
    print(f"  p-value     : {p_anova:.4f}")
    print(f"  Significant : {'YES ✓' if p_anova < 0.05 else 'NO ✗'} (α=0.05)")


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df):,} rows\n")
    plot_win_rate(df)
    plot_cumulative_pnl_by_sentiment(df)
    plot_long_short_ratio(df)
    plot_pnl_boxplot(df)
    plot_coin_sentiment_heatmap(df)
    run_significance_tests(df)
    print("\n✅ Sentiment analysis complete. Charts saved to assets/")
