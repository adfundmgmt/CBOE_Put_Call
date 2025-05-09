  • Top panel: CBOE Total Put/Call Ratio ($CPC)
    – optional simple moving average
    – horizontal lines at 0.80 and 0.95
  • Bottom panel: S&P 500 index ($SPX)
  • Sidebar controls:
        - Sampling period    : Daily or Weekly
        - Years of history   : 1 – 5
        - SMA window (days)  : 0 – 30  (0 = off)

If Yahoo Finance returns a 404 for ^CPC, the script falls back to FRED’s
daily series “PUTCALL”.
"""

import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf
import pandas_datareader.data as web


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page config & sidebar controls
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CPC vs SPX Dashboard", layout="wide")

st.title("CBOE Total Put/Call Ratio ($CPC) vs S&P 500 ($SPX)")

period     = st.sidebar.radio("Sampling period", ["Daily", "Weekly"], index=0)
years_back = st.sidebar.slider("Years of history", 1, 5, value=2)
sma_window = st.sidebar.slider("SMA window (days, 0 = off)", 0, 30, value=10)


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────
def fetch_cpc(start: dt.datetime, end: dt.datetime) -> pd.Series:
    """Try Yahoo '^CPC'; on failure, fall back to FRED 'PUTCALL'."""
    try:
        df = yf.download("^CPC", start=start, end=end, progress=False)
        s = df["Close"].dropna()
        if not s.empty:
            return s
        st.info("Yahoo ^CPC empty — using FRED PUTCALL series.")
    except Exception as err:
        st.info(f"Yahoo ^CPC failed ({err}) — using FRED PUTCALL series.")

    fred = web.DataReader("PUTCALL", "fred", start, end)["PUTCALL"].dropna()
    fred.name = "Close"
    return fred


def fetch_series(ticker: str, start: dt.datetime, end: dt.datetime) -> pd.Series:
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df["Close"].dropna()


def to_weekly(series: pd.Series) -> pd.Series:
    """Resample to Friday closes."""
    return series.resample("W-FRI").last().dropna()


# ─────────────────────────────────────────────────────────────────────────────
# Fetch data
# ─────────────────────────────────────────────────────────────────────────────
end   = dt.datetime.today()
start = end - dt.timedelta(days=365 * years_back + 30)   # 1-month pad

cpc = fetch_cpc(start, end)
spx = fetch_series("^GSPC", start, end)

if period.lower() == "weekly":
    cpc = to_weekly(cpc)
    spx = to_weekly(spx)


# ─────────────────────────────────────────────────────────────────────────────
# Plot
# ─────────────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(12, 8), sharex=True,
    gridspec_kw={"height_ratios": [3, 2]},
)

# CPC line
ax1.plot(cpc.index, cpc, color="navy", linewidth=1.4, label="$CPC")

if sma_window > 0:
    ax1.plot(
        cpc.rolling(sma_window).mean(),
        color="orange", linewidth=1.6,
        label=f"{sma_window}-day SMA",
    )

ax1.axhline(0.80, color="red",   linestyle="--", linewidth=1)
ax1.axhline(0.95, color="green", linestyle="--", linewidth=1)

ax1.set_ylabel("Put/Call Ratio")
ax1.set_title(f"$CPC ({period.lower()}) — last {years_back} yr")
ax1.grid(True, linestyle=":", linewidth=0.5)
ax1.legend(loc="upper right", fontsize=9)

# SPX line
ax2.plot(spx.index, spx, color="black", linewidth=1.4, label="$SPX")
ax2.set_ylabel("S&P 500 Index")
ax2.grid(True, linestyle=":", linewidth=0.5)

plt.tight_layout()
st.pyplot(fig)

st.caption("Data source: Yahoo Finance (fallback to FRED for CPC)")
