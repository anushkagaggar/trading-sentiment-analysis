"""
04_advanced_insights.py
-----------------------
Advanced pattern mining:
  - Smart money accounts (profitable in all conditions)
  - Contrarian signals (Fear → price bounce)
  - Fee drag analysis
  - Monthly rolling sentiment-PnL correlation
Charts saved to assets/advanced_*.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")
COLORS = {"Fear": "#e74c3c", "Greed": "#2ecc71", "Neutral": "#95a5a6"}
SENTIMENT_ORDER = ["Fear", "Neutral", "Greed"]


def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "merged_data.csv"), parse_dates=["Timestamp IST", "Date"])
    df["Is_Profitable"] = df["Closed PnL"] > 0
    return df


# ── 1. Smart Money: accounts profitable in all sentiment regimes ──────────
def identify_smart_money(df):
    closed = df[df["Closed PnL"] != 0]
    acct_sentiment = closed.groupby(["Account", "Sentiment"]).agg(
        Trades=("Closed PnL", "count"),
        Avg_PnL=("Closed PnL", "mean"),
        Win_Rate=("Is_Profitable", "mean"),
        Total_PnL=("Closed PnL", "sum"),
    ).reset_index()

    # Pivot to wide format
    pivot = acct_sentiment.pivot(index="Account", columns="Sentiment", values="Avg_PnL")
    pivot = pivot.dropna()

    # Smart money = positive avg PnL in Fear AND Greed
    smart = pivot[(pivot.get("Fear", 0) > 0) & (pivot.get("Greed", 0) > 0)]
    print(f"\nSmart Money Accounts (positive avg PnL in both Fear & Greed): {len(smart)}")
    print(smart.round(2).to_string())

    # Bar chart: total PnL for smart money vs rest
    total_pnl = closed.groupby("Account")["Closed PnL"].sum().reset_index()
    total_pnl["Category"] = total_pnl["Account"].apply(lambda x: "Smart Money" if x in smart.index else "Rest")
    cat_pnl = total_pnl.groupby("Category")["Closed PnL"].sum()

    fig, ax = plt.subplots(figsize=(7, 5))
    bar_colors = ["#2ecc71" if c == "Smart Money" else "#95a5a6" for c in cat_pnl.index]
    bars = ax.bar(cat_pnl.index, cat_pnl.values, color=bar_colors, edgecolor="white", width=0.4)
    for bar, val in zip(bars, cat_pnl.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500, f"${val:,.0f}", ha="center", fontsize=10)
    ax.set_title("Total PnL: Smart Money vs Rest of Traders", fontsize=13, fontweight="bold")
    ax.set_ylabel("Total Closed PnL (USD)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "advanced_01_smart_money.png"), dpi=150)
    plt.close()
    print("Saved: advanced_01_smart_money.png")
    return smart.index.tolist()


# ── 2. Monthly PnL vs Sentiment Score correlation ─────────────────────────
def plot_monthly_correlation(df):
    closed = df[df["Closed PnL"] != 0].copy()
    closed["YearMonth"] = closed["Date"].dt.to_period("M")

    monthly_pnl = closed.groupby("YearMonth")["Closed PnL"].mean().reset_index()
    monthly_pnl.columns = ["YearMonth", "Avg_PnL"]

    # Encode sentiment numerically: Fear=0, Neutral=1, Greed=2
    sentiment_map = {"Fear": 0, "Neutral": 1, "Greed": 2}
    closed["Sentiment_Score"] = closed["Sentiment"].map(sentiment_map)
    monthly_sentiment = closed.groupby("YearMonth")["Sentiment_Score"].mean().reset_index()
    monthly_sentiment.columns = ["YearMonth", "Avg_Sentiment"]

    monthly = monthly_pnl.merge(monthly_sentiment, on="YearMonth")
    monthly["YearMonth_dt"] = monthly["YearMonth"].dt.to_timestamp()

    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax2 = ax1.twinx()

    ax1.bar(monthly["YearMonth_dt"], monthly["Avg_PnL"], color="#3498db", alpha=0.6, label="Avg Monthly PnL", width=20)
    ax2.plot(monthly["YearMonth_dt"], monthly["Avg_Sentiment"], color="#e67e22", linewidth=2, marker="o", markersize=4, label="Avg Sentiment Score")

    ax1.set_ylabel("Avg PnL per Trade (USD)", color="#3498db")
    ax2.set_ylabel("Avg Sentiment (0=Fear, 1=Neutral, 2=Greed)", color="#e67e22")
    ax1.set_title("Monthly Avg PnL vs Market Sentiment Over Time", fontsize=13, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "advanced_02_monthly_pnl_vs_sentiment.png"), dpi=150)
    plt.close()
    print("Saved: advanced_02_monthly_pnl_vs_sentiment.png")

    corr = monthly["Avg_PnL"].corr(monthly["Avg_Sentiment"])
    print(f"\nPearson correlation (monthly PnL vs Sentiment Score): {corr:.4f}")


# ── 3. Contrarian signal: PnL of trades opened during Fear ────────────────
def plot_contrarian_fear_signal(df):
    """
    Compares PnL of Open Long positions that were initiated during Fear
    vs those opened during Greed — tests contrarian thesis
    """
    opens = df[df["Direction"] == "Open Long"].copy()
    opens["Sentiment"] = pd.Categorical(opens["Sentiment"], categories=SENTIMENT_ORDER, ordered=True)

    # For each account, look at subsequent close PnL by sentiment of open
    # Proxy: Closed PnL of Close Long trades on same day as Fear open days
    fear_dates = set(df[df["Sentiment"] == "Fear"]["Date"].dt.date)
    greed_dates = set(df[df["Sentiment"] == "Greed"]["Date"].dt.date)

    closes = df[df["Direction"] == "Close Long"].copy()
    closes["Open_Date"] = closes["Date"].dt.date

    fear_closes = closes[closes["Open_Date"].isin(fear_dates)]["Closed PnL"]
    greed_closes = closes[closes["Open_Date"].isin(greed_dates)]["Closed PnL"]

    fig, ax = plt.subplots(figsize=(9, 5))
    data = [fear_closes.clip(-2000, 2000), greed_closes.clip(-2000, 2000)]
    bp = ax.boxplot(data, labels=["Closed During\nFear Periods", "Closed During\nGreed Periods"],
                    patch_artist=True, notch=False)
    bp["boxes"][0].set_facecolor(COLORS["Fear"])
    bp["boxes"][1].set_facecolor(COLORS["Greed"])
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Close Long PnL: Fear vs Greed Market Periods\n(Contrarian Signal Check)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Closed PnL (USD, clipped ±$2K)")

    # Annotate medians
    for i, d in enumerate([fear_closes, greed_closes]):
        med = d.median()
        ax.text(i + 1, med + 30, f"Median: ${med:.0f}", ha="center", fontsize=9, color="navy")

    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "advanced_03_contrarian_signal.png"), dpi=150)
    plt.close()
    print("Saved: advanced_03_contrarian_signal.png")


# ── 4. Fee drag by sentiment ──────────────────────────────────────────────
def plot_fee_drag(df):
    fee_analysis = df.groupby("Sentiment").agg(
        Total_Fee=("Fee", "sum"),
        Total_PnL=("Closed PnL", "sum"),
        Avg_Fee_Per_Trade=("Fee", "mean"),
    ).reindex(SENTIMENT_ORDER)
    fee_analysis["Fee_as_Pct_of_PnL"] = (fee_analysis["Total_Fee"] / fee_analysis["Total_PnL"].abs() * 100).round(1)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(fee_analysis.index, fee_analysis["Avg_Fee_Per_Trade"],
                color=[COLORS[s] for s in fee_analysis.index], edgecolor="white", width=0.5)
    axes[0].set_title("Avg Fee per Trade by Sentiment", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Avg Fee (USD)")

    axes[1].bar(fee_analysis.index, fee_analysis["Fee_as_Pct_of_PnL"],
                color=[COLORS[s] for s in fee_analysis.index], edgecolor="white", width=0.5)
    axes[1].set_title("Total Fees as % of Absolute PnL", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Fee Drag (%)")
    axes[1].yaxis.set_major_formatter(mticker.PercentFormatter())

    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "advanced_04_fee_drag.png"), dpi=150)
    plt.close()
    print("Saved: advanced_04_fee_drag.png")
    print("\nFee Drag Summary:")
    print(fee_analysis.to_string())


# ── 5. Account performance heatmap across sentiments ─────────────────────
def plot_account_heatmap(df):
    closed = df[df["Closed PnL"] != 0]
    acct_pivot = closed.groupby(["Account", "Sentiment"])["Closed PnL"].mean().unstack(fill_value=0)
    acct_pivot = acct_pivot.reindex(columns=SENTIMENT_ORDER, fill_value=0)

    # Shorten account labels
    acct_pivot.index = [f"{a[:6]}...{a[-4:]}" for a in acct_pivot.index]
    acct_pivot = acct_pivot.sort_values("Greed", ascending=False)

    fig, ax = plt.subplots(figsize=(8, 9))
    sns.heatmap(acct_pivot, annot=True, fmt=".0f", cmap="RdYlGn", center=0, ax=ax,
                linewidths=0.5, cbar_kws={"label": "Avg PnL per Trade (USD)"})
    ax.set_title("Avg PnL per Trade: Account × Sentiment", fontsize=13, fontweight="bold")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Account")
    plt.tight_layout()
    plt.savefig(os.path.join(ASSETS_DIR, "advanced_05_account_heatmap.png"), dpi=150)
    plt.close()
    print("Saved: advanced_05_account_heatmap.png")


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df):,} rows\n")
    identify_smart_money(df)
    plot_monthly_correlation(df)
    plot_contrarian_fear_signal(df)
    plot_fee_drag(df)
    plot_account_heatmap(df)
    print("\n✅ Advanced analysis complete. Charts saved to assets/")
