# cpc_spx_simple.py
import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Simple CPC vs SPX", layout="wide")
st.title("CBOE Total Put/Call Ratio ($CPC) vs S&P 500 ($SPX)")

# ── Sidebar controls ───────────────────────────────────────────────────────
period     = st.sidebar.radio("Period", ["Daily", "Weekly"], index=0)
years_back = st.sidebar.slider("Years of history", 1, 5, value=2)
sma_window = st.sidebar.slider("SMA window (0 = off)", 0, 30, value=10)

# ── Download data with yfinance ────────────────────────────────────────────
end   = dt.datetime.today()
start = end - dt.timedelta(days=365 * years_back + 30)

cpc = yf.download("^CPC", start=start, end=end, progress=False)["Close"].dropna()
spx = yf.download("^GSPC", start=start, end=end, progress=False)["Close"].dropna()

if period == "Weekly":
    cpc = cpc.resample("W-FRI").last().dropna()
    spx = spx.resample("W-FRI").last().dropna()

if cpc.empty:
    import pandas_datareader.data as web

    st.info("Yahoo ^CPC returned no data — pulling from FRED instead.")
    fred = web.DataReader("PUTCALL", "fred", start, end)["PUTCALL"].dropna()
    fred.name = "Close"
    cpc = fred

# ── Plot ───────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
)

ax1.plot(cpc.index, cpc, color="navy", linewidth=1.4, label="$CPC")

if sma_window > 0:
    ax1.plot(cpc.rolling(sma_window).mean(),
             color="orange", linewidth=1.6,
             label=f"{sma_window}-day SMA")

ax1.axhline(0.80, color="red", linestyle="--", linewidth=1)
ax1.axhline(0.95, color="green", linestyle="--", linewidth=1)
ax1.set_ylabel("Put/Call Ratio")
ax1.set_title(f"{period} data — last {years_back} year(s)")
ax1.grid(True, linestyle=":", linewidth=0.5)
ax1.legend(loc="upper right", fontsize=9)

ax2.plot(spx.index, spx, color="black", linewidth=1.4)
ax2.set_ylabel("S&P 500 Index")
ax2.grid(True, linestyle=":", linewidth=0.5)

plt.tight_layout()
st.pyplot(fig)
