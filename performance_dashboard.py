import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Performance Dashboard", layout="wide")

st.title("📊 Katılım Momentum – Performance Dashboard")

# --- VERİYİ OKU ---
try:
    df = pd.read_csv("equity_history.csv")
except:
    st.error("equity_history.csv bulunamadı.")
    st.stop()

if df.empty:
    st.warning("Henüz veri yok.")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")

# --- EQUITY HESAPLAMA ---
df["Peak"] = df["Equity"].cummax()
df["Drawdown"] = 1 - (df["Equity"] / df["Peak"])

start_equity = df["Equity"].iloc[0]
current_equity = df["Equity"].iloc[-1]

total_return = (current_equity / start_equity) - 1
max_dd = df["Drawdown"].max()

days = len(df)
if days > 1:
    cagr = (1 + total_return) ** (252 / days) - 1
else:
    cagr = 0

# --- ÜST METRİKLER ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Başlangıç Sermaye", f"{start_equity:.2f} TL")
col2.metric("Güncel Sermaye", f"{current_equity:.2f} TL")
col3.metric("Toplam Getiri", f"%{total_return*100:.2f}")
col4.metric("Max Drawdown", f"%{max_dd*100:.2f}")

st.metric("CAGR (Yaklaşık)", f"%{cagr*100:.2f}")

# --- EQUITY GRAFİĞİ ---
st.subheader("📈 Equity Eğrisi")

fig1, ax1 = plt.subplots()
ax1.plot(df["Date"], df["Equity"])
ax1.set_xlabel("Tarih")
ax1.set_ylabel("Equity (TL)")
st.pyplot(fig1)

# --- DRAWDOWN GRAFİĞİ ---
st.subheader("📉 Drawdown Grafiği")

fig2, ax2 = plt.subplots()
ax2.fill_between(df["Date"], df["Drawdown"], 0)
ax2.set_xlabel("Tarih")
ax2.set_ylabel("Drawdown")
st.pyplot(fig2)

# --- GÜNLÜK GETİRİ ---
df["Daily_Return"] = df["Equity"].pct_change()

avg_daily_return = df["Daily_Return"].mean()
std_daily_return = df["Daily_Return"].std()

if pd.isna(avg_daily_return) or pd.isna(std_daily_return) or std_daily_return == 0:
    sharpe = 0
else:
    sharpe = (avg_daily_return / std_daily_return) * np.sqrt(252)

if max_dd != 0:
    calmar = cagr / max_dd
else:
    calmar = 0

st.subheader("📊 Risk Metrikleri")

col1, col2, col3 = st.columns(3)
col1.metric("Sharpe Ratio", f"{sharpe:.2f}")
col2.metric("Calmar Ratio", f"{calmar:.2f}")
if pd.isna(avg_daily_return):
    avg_display = 0
else:
    avg_display = avg_daily_return * 100

col3.metric("Ortalama Günlük Getiri", f"%{avg_display:.2f}")

# --- GETİRİ DAĞILIMI ---
st.subheader("📈 Günlük Getiri Dağılımı")

fig3, ax3 = plt.subplots()
ax3.hist(df["Daily_Return"].dropna(), bins=30)
ax3.set_xlabel("Günlük Getiri")
ax3.set_ylabel("Frekans")
st.pyplot(fig3)

# --- AYLIK GETİRİ ANALİZİ ---

st.subheader("📅 Aylık Getiri Analizi")

monthly = df.copy()
monthly = monthly.set_index("Date")
monthly_equity = monthly["Equity"].resample("M").last()
monthly_returns = monthly_equity.pct_change()

if len(monthly_returns.dropna()) > 0:

    positive_months = (monthly_returns > 0).sum()
    negative_months = (monthly_returns < 0).sum()
    avg_monthly = monthly_returns.mean()
    best_month = monthly_returns.max()
    worst_month = monthly_returns.min()

    col1, col2, col3 = st.columns(3)
    col1.metric("Pozitif Ay", int(positive_months))
    col2.metric("Negatif Ay", int(negative_months))
    col3.metric("Ortalama Aylık Getiri", f"%{avg_monthly*100:.2f}")

    col4, col5 = st.columns(2)
    col4.metric("En İyi Ay", f"%{best_month*100:.2f}")
    col5.metric("En Kötü Ay", f"%{worst_month*100:.2f}")

    monthly_table = monthly_returns.to_frame(name="Aylık Getiri")
    monthly_table.index = monthly_table.index.strftime("%Y-%m")

    st.dataframe(monthly_table)

else:
    st.info("Henüz aylık veri oluşmadı.")

# --- BENCHMARK KARŞILAŞTIRMA (XU100) ---

import yfinance as yf

st.subheader("📊 Benchmark Karşılaştırma (XU100)")

start_date = df["Date"].iloc[0]

try:
    xu100 = yf.download("XU100.IS", start=start_date)
    xu100 = xu100["Close"].pct_change().fillna(0)
    xu100_cum = (1 + xu100).cumprod()

    strategy_returns = df.set_index("Date")["Equity"].pct_change().fillna(0)
    strategy_cum = (1 + strategy_returns).cumprod()

    fig4, ax4 = plt.subplots()
    ax4.plot(strategy_cum, label="Katılım Momentum")
    ax4.plot(xu100_cum, label="XU100")
    ax4.legend()
    ax4.set_title("Strateji vs XU100")

    st.pyplot(fig4)

except:
    st.warning("XU100 verisi çekilemedi.")

# --- ALPHA & BETA HESAPLAMA ---

st.subheader("📈 Alpha & Beta Analizi")

# Günlük getirileri hizala
common_index = strategy_returns.index.intersection(xu100.index)

aligned_strategy = strategy_returns.loc[common_index]
aligned_xu100 = xu100.loc[common_index]

if len(aligned_strategy) > 1:

    covariance = np.cov(aligned_strategy, aligned_xu100)
    beta = covariance[0][1] / covariance[1][1] if covariance[1][1] != 0 else 0

    alpha = aligned_strategy.mean() - beta * aligned_xu100.mean()

    col1, col2 = st.columns(2)
    col1.metric("Beta", f"{beta:.2f}")
    col2.metric("Alpha (Günlük)", f"{alpha*100:.4f}%")

else:
    st.info("Alpha & Beta hesaplamak için yeterli veri yok.")