# cpc_spx_simple.py
import datetime as dt
import io
import urllib.request

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Simple CPC vs SPX", layout="wide")
st.title("CBOE Total Put/Call Ratio ($CPC) vs S&P-500 ($SPX)")

# ── Sidebar controls ───────────────────────────────────────────────────────
period     = st.sidebar.radio("Period", ["Daily", "Weekly"], index=0)
years_back = st.sidebar.slider("Years of history", 1, 5, value=2)
sma_window = st.sidebar.slider("SMA window (0 = off)", 0, 30, value=10)

# ── Date range ──────────────────────────────────────────────────────────────
end   = dt.datetime.today()
start = end - dt.timedelta(days=365 * years_back + 30)   # pad 1 mth for SMA

# ── Download CPC & SPX from Yahoo ───────────────────────────────────────────
cpc = yf.download("^CPC", start=start, end=end, progress=False)["Close"].dropna()
spx = yf.download("^GSPC", start=start, end=end, progress=False)["Close"].dropna()

# ── Fallback to FRED if Yahoo is empty ─────────────────────────────
if cpc.empty:
    st.info("Yahoo ^CPC empty — downloading daily PUTCALL series from FRED.")

    fred_url = (
        "https://fred.stlouisfed.org/series/PUTCALL/downloaddata/PUTCALL.csv"
    )

    try:
        fred = pd.read_csv(
            fred_url,
            skiprows=range(1, 12),      # first 11 rows are metadata comments
            parse_dates=["DATE"],
            index_col="DATE",
        )["VALUE"].astype("float")
        fred.name = "Close"
        cpc = fred.loc[start:end].dropna()

    except Exception as err:
        st.error(f"FRED download failed ({err}). No CPC data available.")
        st.stop()


# ── Resample to weekly if selected ─────────────────────────────────────────
if period == "Weekly":
    cpc = cpc.resample("W-FRI").last().dropna()
    spx = spx.resample("W-FRI").last().dropna()

# ── Plot ───────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
)

# CPC line
ax1.plot(cpc.index, cpc, color="navy", linewidth=1.4, label="$CPC")

if sma_window > 0:
    ax1.plot(cpc.rolling(sma_window).mean(),
             color="orange", linewidth=1.6,
             label=f"{sma_window}-day SMA")

ax1.axhline(0.80, color="red",   linestyle="--", linewidth=1)
ax1.axhline(0.95, color="green", linestyle="--", linewidth=1)
ax1.set_ylabel("Put/Call Ratio")
ax1.set_title(f"{period} data — last {years_back} year(s)")
ax1.grid(True, linestyle=":", linewidth=0.5)
ax1.legend(loc="upper right", fontsize=9)

# SPX line
ax2.plot(spx.index, spx, color="black", linewidth=1.4)
ax2.set_ylabel("S&P-500 Index")
ax2.grid(True, linestyle=":", linewidth=0.5)

plt.tight_layout()
st.pyplot(fig)
