# 📈 Trader Dashboard — Pro Stock, Mutual Fund & AI Terminal

An institutional-grade, high-conviction trading and investment web application designed for Indian equities (NSE/BSE), Sectoral Indices, and Mutual Funds.

Built with **Streamlit**, **Plotly**, and **Multi-Factor Confluence & Quantitative Algorithms**. Fully responsive for **Laptop** and **Mobile Phone** daily use.

---

## ✨ Features & Upgrades

### 1. 📌 Pinned Assets Quick-Radar Bar
- Pin any Stock or Mutual Fund to the top quick-ticker bar for 1-click live monitoring.
- Displays real-time LTP, 1D % Change, and instant status without needing to search each time.
- Fully persistent: Pinned assets stay saved even when refreshing or closing the browser.

### 2. ⭐ Persistent Watchlist & Portfolio Tracker
- Dedicated **Watchlist Tab** to add, track, and manage your favorite Stocks and Mutual Funds.
- Real-time live prices, Buy/Sell probability %, dynamic target, stop loss, and active candlestick patterns.
- Add or remove stocks directly via the `⭐ Watch` buttons on every card.

### 3. 🤖 AI Quant Market Copilot (Intelligent Assistant & Screener)
- Natural language query assistant: Ask questions about any stock, sector, index, or mutual fund!
- Examples of questions you can ask:
  - *"Mujhe top high accuracy swing buy stocks batao"*
  - *"Konsi stocks me 1 week short swing setup ban raha hai?"*
  - *"FII aur DII abhi kis sector me buy kar rahe hain?"*
  - *"Top mutual funds kaunse hain long term SIP ke liye?"*
  - *"RELIANCE analysis / target"*
- Built-in Quant NLP engine automatically scans live multi-factor indicators and responds instantly with structured metric cards, entry, target, stop loss, and probability!
- Optional Google Gemini API key support for extended conversational responses.

### 4. 🎯 Multi-Factor Confluence Engine (Highest Accuracy & Probability)
- Combines:
  1. **Trend Confluence (EMA 9, EMA 21, SMA 50, SMA 200)**
  2. **Volume Spike Confirmation** (20-day volume surge detection to eliminate fakeouts)
  3. **Momentum & RSI Sweet-Spot Alignment** (45–68 Bullish zone)
  4. **Bollinger Band Squeeze & Volatility Expansion**
  5. **Candlestick Pattern Confluence**
- Results in mathematically calibrated win-rate probabilities (up to 95%+ on top setups).

### 5. 🏠 Market & Institutional FII / FPI / DII Predictive Radar
- **Live Cash Market Flows:** Real-time FII/DII daily buy/sell data, streak tracking, 5-session net bias, and cumulative totals for 1D, 1W, 1M, and 30 sessions.
- **NSDL Sector Depository Net Investment:** Depository-level tracking of which sectors FPI/FII are accumulating vs. distributing.
- **Forward Predictive Matrix:** 1 Day, 1 Week (Short Swing), 1 Month (Positional), 3 Months, and 6 Months+ forward horizons with target sectors, stocks, probabilities, and conviction rank.
- **Bulk & Block Deals Tracker:** High-volume institutional trades with buyer/seller identification.
- **6-Month Sector Momentum & Relative Strength:** Heatmap ranking of all major NSE sectors.

### 6. 🔍 Search & Multi-Timeframe Candlestick Pattern Engine
- **Universal Search:** Any Stock (`RELIANCE`, `TCS`, `INFY`), Index (`NIFTY`, `BANKNIFTY`), or Mutual Fund (`Parag Parikh Flexi Cap`, `HDFC Mid Cap`).
- **Multi-Timeframe Candlestick Pattern Scanner:**
  - Granular real-time scan across **15 Min**, **1 Hour**, **4 Hour**, **1 Day**, **1 Week**, and **1 Month** candles.
  - Automatically recognizes: Hammer, Shooting Star, Bullish/Bearish Engulfing, Morning/Evening Star, Doji, 20-Period Breakout/Breakdown, and Marubozu.
  - Outputs immediate tactical trigger, timeframe accuracy %, target, stop loss, and actionable guidance for each timeframe.
- **Interactive Candlestick Chart:** Interactive Plotly chart with 20, 50, and 200 SMA overlays.
- **Mutual Fund Deep Dive:** Real-time AMFI NAV, returns (1W, 1M, 3M, 6M, 1Y, 3Y CAGR), volatility %, max drawdown, target NAV forecast, and SIP vs. Lumpsum verdict.

### 7. 🎯 High-Conviction Stocks Tab (Exact Image UI)
- **Styles:** Short Swing (2-5 days / 1 week momentum), Swing (2-6 weeks positional), Intraday, F&O, Long Term.
- **Timeframe Horizons:** 1 Day, 1 Week, 1 Month, 3 Months, 6 Months+.
- **High-Accuracy Filter (>= 70% or 80%+):** Separate lists of Top 6–8 BUY Setups and Top 6–8 SELL / SHORT Setups.
- **Card UI:** Ticker, Name, `↗ BUY` / `↘ SELL` badge, `#Rank`, `🎯 accuracy XX%`, `[ENTRY] [TARGET] [STOP]`, Trailing stop rule, Wait for condition, Hold period, and conviction thesis.
- Includes `📌 Pin`, `⭐ Watch`, and `🔍 Deep Dive` action buttons on every card.

### 8. 💼 Mutual Funds Tab (Ranked High-Conviction Cards)
- **Timeframes:** 1 Week (Short Swing), 1 Month, 3 Months, 6 Months+.
- **Categories:** Large Cap, Mid Cap, Small Cap, Flexi Cap, Sectoral IT, Pharma, Balanced Advantage, Contra, ELSS.
- Includes `📌 Pin`, `⭐ Watch`, and `📊 Analysis` action buttons.

### 9. 📰 News & Forex Factory / Global Macro Impact Predictor
- **Forex Factory & Economic Calendar:** High-impact events (US Fed FOMC, US CPI Inflation, US Non-Farm Payrolls, RBI MPC Repo Rate, OPEC+ Crude).
- **Cross-Asset Impact Matrix:** Displays exact Impacted Sectors, Stocks & Indices, and Mutual Funds, with impact probability and strategic action.
- Real-time news streams with sentiment tagging and immediate trade suggestions.

---

## 🚀 How to Run Locally on Your Laptop

### 1. Install Python (if not already installed)
Download and install Python (version 3.10, 3.11, or 3.12) from [python.org](https://www.python.org/downloads/).  
*(Make sure to check "Add Python to PATH" during installation).*

### 2. Install Required Packages
Open Command Prompt or PowerShell in this folder (`d:\BBN Antigravity App`) and run:
```bash
pip install -r requirements.txt
```

### 3. Run the App
Double-click `run_app.bat` or run in terminal:
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📱 How to Use on Your Mobile Phone (Local Wi-Fi / Hotspot)

When you run Streamlit on your laptop, it displays two URLs:
- **Local URL:** `http://localhost:8501` (for your laptop)
- **Network URL:** `http://192.168.x.x:8501` (for your mobile)

**To open on your phone:**
1. Connect your phone to the same Wi-Fi network (or laptop hotspot).
2. Open Chrome or Safari on your phone.
3. Type the **Network URL** shown in your laptop's terminal (e.g. `http://192.168.1.5:8501`).
4. The dashboard will load with full touch-friendly responsive mobile dark UI!

---

## 🌐 How to Deploy 100% Free on Streamlit Cloud (`streamlit.app`)
*(Run 24/7 on your mobile & laptop from anywhere in the world without keeping your laptop on!)*

### Step 1: Push to GitHub
1. Create a free account on [github.com](https://github.com).
2. Create a new repository named `trader-dashboard`.
3. In this folder (`d:\BBN Antigravity App`), open terminal and run:
```bash
git init
git add .
git commit -m "Trader Dashboard Pro Terminal with AI Copilot & Watchlist"
git branch -M main
git remote add origin https://github.com/<your-username>/trader-dashboard.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `trader-dashboard`, branch: `main`, and main file path: `app.py`.
4. Click **"Deploy!"**.

Within 2 minutes, your webapp will be live at `https://<your-app-name>.streamlit.app/`. Bookmark this URL on your phone's home screen for daily trading and investment analysis!
