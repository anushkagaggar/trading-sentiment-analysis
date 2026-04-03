# Bitcoin Sentiment × Hyperliquid Trader Performance Analysis

> **Assignment:** Explore the relationship between market sentiment (Fear/Greed Index) and trader performance on Hyperliquid. Uncover hidden patterns and deliver actionable insights.

---

## 📁 Repository Structure

```
trading-sentiment-analysis/
│
├── data/                        # Place raw CSV/XLSX datasets here
│   ├── historical_data.xlsx     # Hyperliquid trader data
│   └── fear_greed_index.csv     # Bitcoin Fear & Greed Index
│
├── src/
│   ├── 01_data_preprocessing.py # Data cleaning & merging
│   ├── 02_eda.py                # Exploratory Data Analysis
│   ├── 03_sentiment_analysis.py # Sentiment vs performance deep dive
│   └── 04_advanced_insights.py  # Advanced pattern mining
│
├── reports/
│   └── analysis_report.md       # Full written analytical report
│
├── assets/                      # Charts and visualizations (screenshots)
│
├── requirements.txt
└── README.md
```

---

## 🗂️ Datasets

| Dataset | Rows | Period | Key Columns |
|---|---|---|---|
| Hyperliquid Trader Data | 211,224 | Jan 2023 – Dec 2025 | Account, Coin, Side, Direction, Closed PnL, Fee, Execution Price |
| Fear & Greed Index | ~1000 | Daily | Date, Classification (Fear / Greed) |

---

## 🚀 Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/trading-sentiment-analysis.git
cd trading-sentiment-analysis

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add datasets to data/ folder

# 4. Run scripts in order
python src/01_data_preprocessing.py
python src/02_eda.py
python src/03_sentiment_analysis.py
python src/04_advanced_insights.py
```

All charts are saved automatically to `assets/`.

---

## 🔍 Key Research Questions

1. Do traders perform better (higher PnL) during Fear or Greed periods?
2. Are traders more aggressive (larger positions) during Greed?
3. Which coins are traded most during extreme fear vs extreme greed?
4. Do Open Long vs Open Short ratios shift with sentiment?
5. Which accounts consistently profit regardless of sentiment?
6. Are fees (drag on performance) higher during volatile sentiment regimes?

---

## 📊 Key Findings Summary

See [`reports/analysis_report.md`](reports/analysis_report.md) for full insights.

**Highlights:**
- Greed phases correlate with higher trade volumes and larger position sizes
- Fear phases show more Short-opening behavior and lower average PnL
- A small subset of "smart money" accounts remain profitable across all sentiment regimes
- Extreme Fear is often a contrarian buy signal — best performing closes happen post-Fear

---

## 🛠️ Tech Stack

- **Python 3.10+**
- pandas, numpy — data manipulation
- matplotlib, seaborn — visualizations
- scipy — statistical testing

---

## 📬 Submission

Submitted as part of Round-0 assignment for Anything.ai / Primetrade.ai Data Science role.
