import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import pandas_datareader.data as web

###############################################################################
# Streamlit config
###############################################################################
st.set_page_config(page_title="CPC vs SPX Dashboard", layout="wide")

st.title("CBOE Total Put/Call Ratio ($CPC) vs S&P 500 ($SPX)")

###############################################################################
# Sidebar controls
###############################################################################
period = st.sidebar.radio("Sampling period", ["Daily", "Weekly"], index=0)
years_back = st.sidebar.slider("Years of history", 1, 5, 2)
sma_window = st.sidebar.slider("SMA window (days, 0 = off)", 0, 30, 10)

###############################################################################
# Data helpers
###############################################################################
def fetch_cpc(start: dt.datetime, end: dt.datetime) -> pd.Series:
    \"\"\"Download CPC, fallback to FRED PUTCALL.\"\"\"
    try:
        df = yf.download("^CPC", start=start, end=end, progress=False)
        s = df["Close"].dropna()
        if not s.empty:
            return s
        st.info("Yahoo ^CPC empty; using FRED PUTCALL series.")
    except Exception as err:
        st.info(f"Yahoo ^CPC failed ({err}); using FRED PUTCALL series.")
    fred = web.DataReader("PUTCALL", "fred", start, end)["PUTCALL"].dropna()
    fred.name = "Close"
    return fred

def fetch_series(ticker: str, start: dt.datetime, end: dt.datetime) -> pd.Series:
    df = yf.download(ticker, start=start, end=end, progress=False)
    return df["Close"].dropna()

def resample_weekly(series: pd.Series) -> pd.Series:
    return series.resample("W-FRI").last().dropna()

###############################################################################
# Fetch data
###############################################################################
end = dt.datetime.today()
start = end - dt.timedelta(days=365 * years_back + 30)

cpc = fetch_cpc(start, end)
spx = fetch_series("^GSPC", start, end)

if period.lower() == "weekly":
    cpc = resample_weekly(cpc)
    spx = resample_weekly(spx)

###############################################################################
# Plot
###############################################################################
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                               gridspec_kw={"height_ratios": [3, 2]})

# CPC line
ax1.plot(cpc.index, cpc, color="navy", linewidth=1.4, label="$CPC")

if sma_window > 0:
    ax1.plot(cpc.rolling(sma_window).mean(), color="orange",
             linewidth=1.6, label=f"{sma_window}-day SMA")

# Thresholds
ax1.axhline(0.80, color="red", linestyle="--", linewidth=1)
ax1.axhline(0.95, color="green", linestyle="--", linewidth=1)

ax1.set_ylabel("Put/Call Ratio")
ax1.set_title(f"$CPC ({period.lower()}) — last {years_back} yr")
ax1.grid(True, linestyle=":", linewidth=0.5)
ax1.legend(loc="upper right", fontsize=9)

# SPX panel
ax2.plot(spx.index, spx, color="black", linewidth=1.4, label="$SPX")
ax2.set_ylabel("S&P 500 Index")
ax2.grid(True, linestyle=":", linewidth=0.5)

plt.tight_layout()

st.pyplot(fig)

st.caption("Data source: Yahoo Finance (fallback to FRED for CPC).")
"""

from pathlib import Path
Path("/mnt/data/cpc_spx_streamlit.py").write_text(streamlit_code)

"/mnt/data/cpc_spx_streamlit.py"
