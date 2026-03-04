from portfolio_engine import load_cash, load_portfolio, calculate_equity
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json

st.set_page_config(page_title="Katılım Momentum Sistemi", layout="wide")
st.title("📈 Katılım Momentum Sistemi")

tab1, tab2, tab3 = st.tabs(["📊 Canlı Portföy", "📈 Momentum Analiz", "📚 Backtest"])

# ==========================================================
# 📊 TAB 1 — CANLI PORTFÖY
# ==========================================================

with tab1:

    st.markdown("## 🛡 Risk Paneli")

    try:
        with open("risk_state.json", "r") as f:
            risk_data = json.load(f)

        if risk_data["freeze"]:
            st.error("🚨 SİSTEM FREEZE MODUNDA")
        else:
            st.success("✅ Sistem Normal Çalışıyor")

        st.write(f"Peak Equity: {risk_data['peak_equity']:.2f}")

    except:
        st.info("Risk verisi bulunamadı.")

    st.markdown("## 📊 Canlı Portföy Durumu")

    cash = load_cash()
    portfolio = load_portfolio()

    st.write(f"💰 Nakit: {cash:.2f} TL")

    if portfolio.empty:
        st.write("Portföy boş.")

    else:
        st.dataframe(portfolio)

        tickers = portfolio["Stock"].tolist()
        data = yf.download(tickers, period="5d")
        close_prices = data["Close"].iloc[-1]

        if isinstance(close_prices, pd.Series):
            market_prices = close_prices.to_dict()
        else:
            market_prices = {tickers[0]: float(close_prices)}

        equity = calculate_equity(market_prices)
        st.write(f"📈 Toplam Equity: {equity:.2f} TL")

        st.markdown("## 📈 Teknik Görünüm (Destek / Direnç)")

        for _, row in portfolio.iterrows():

            stock = row["Stock"]
            entry = float(row["EntryPrice"])
            stop = float(row["Stop"])

            st.markdown(f"### {stock}")

            data_chart = yf.download(stock, period="3mo")
            close_chart = data_chart["Close"].squeeze()

            current_price = float(close_chart.iloc[-1])

            # ===== KAR ZARAR HESABI =====
            pnl_pct = ((current_price - entry) / entry) * 100
            pnl_tl = (current_price - entry) * row["Lot"]

            # ===== RİSK & HEDEF =====
            risk_per_share = entry - stop
            target_2R = entry + (risk_per_share * 2)

            if pnl_pct >= 0:
                st.success(f"🟢 KAR: {pnl_pct:.2f}% | {pnl_tl:.2f} TL")
            else:
                st.error(f"🔴 ZARAR: {pnl_pct:.2f}% | {pnl_tl:.2f} TL")

            st.write(f"Risk (Lot Başına): {risk_per_share:.2f}")
            st.write(f"2R Hedef: {target_2R:.2f}")

            resistance = float(close_chart.rolling(20).max().iloc[-1])
            support = float(close_chart.rolling(20).min().iloc[-1])

            st.write(f"Güncel: {current_price:.2f}")
            st.write(f"Giriş: {entry:.2f}")
            st.write(f"Stop: {stop:.2f}")
            st.write(f"20 Günlük Direnç: {resistance:.2f}")
            st.write(f"20 Günlük Destek: {support:.2f}")

            chart_df = pd.DataFrame({
                "Close": close_chart,
                "Direnç": close_chart.rolling(20).max(),
                "Destek": close_chart.rolling(20).min()
            })

            st.line_chart(chart_df)
            st.markdown("---")

    st.markdown("### 📝 Sistem Logları")

    try:
        with open("system_log.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()
            st.text("".join(logs[-20:]))
    except:
        st.write("Henüz log yok.")

    st.markdown("## 📊 Equity Eğrisi")

    try:
        history_df = pd.read_csv("equity_history.csv")
        history_df["Date"] = pd.to_datetime(history_df["Date"])
        history_df.set_index("Date", inplace=True)

        st.line_chart(history_df["Equity"])

    except:
        st.info("Equity history henüz oluşmadı.")    


# ==========================================================
# 📈 TAB 2 — MOMENTUM ANALİZ
# ==========================================================


with tab2:

    st.markdown("## 🚀 Production Aktif Top7")

    try:
        prod_top7 = pd.read_csv("top7_current.csv")
        st.dataframe(prod_top7)
    except:
        st.warning("Henüz production rebalance yapılmadı.")

    st.markdown("## 📈 Momentum Top 7 Analiz")

    from universe import katilim_list

    data = yf.download(katilim_list, start="2020-01-01")
    close = data["Close"].dropna(axis=1, how="all")

    momentum = close.pct_change(60)
    momentum_monthly = momentum.resample("ME").last()

    with open("rebalance_flag.json", "r") as f:
        flag_data = json.load(f)

    active_month = flag_data["last_rebalance"]

    matching_month = momentum_monthly[
        momentum_monthly.index.strftime("%Y-%m") == active_month
    ]

    if not matching_month.empty:
        last_date = matching_month.index[0]
    else:
        # Eğer aktif ay henüz kapanmadıysa son mevcut ayı kullan
        last_date = momentum_monthly.index[-1]
        st.info("Aktif ay henüz kapanmadı. Son tamamlanan ay kullanılıyor.")

    last_ranks = momentum_monthly.loc[last_date].rank(ascending=False)
    top7 = last_ranks.sort_values().head(7)

    st.markdown("## 🔍 Production vs Analiz Karşılaştırma")

    try:
        prod_top7 = pd.read_csv("top7_current.csv")
        prod_list = prod_top7["Stock"].tolist()
        analiz_list = top7.index.tolist()

        compare_df = pd.DataFrame({
            "Production": prod_list,
            "Analiz": analiz_list
        })

        compare_df["Durum"] = compare_df.apply(
            lambda x: "✅ Aynı" if x["Production"] == x["Analiz"] else "❌ Farklı",
            axis=1
        )

        st.dataframe(compare_df)

    except:
        st.info("Production listesi henüz oluşmadı.")

    st.subheader(f"Canlı Ay: {last_date.date()}")
    st.dataframe(top7)

    # ================================
    # 📊 TOP7 PERFORMANS TAKİBİ
    # ================================

    st.markdown("## 📊 Top7 Performans Takibi")

    # Ayın ilk işlem günü fiyatı
    month_start = close.resample("MS").first()

    # Son ayın başlangıç tarihi
    current_month = last_date

    if current_month in month_start.index:

        start_prices = month_start.loc[current_month, top7.index]
        current_prices = close.loc[close.index[-1], top7.index]

        performance_df = pd.DataFrame()

        # Sistem sırası (momentum sırası)
        performance_df["Sistem Sırası"] = top7.rank()

        performance_df["Ay Başı Fiyat"] = start_prices
        performance_df["Güncel Fiyat"] = current_prices

        performance_df["% Değişim"] = (
            (current_prices - start_prices) / start_prices
        ) * 100

        # Gerçek performans sırası
        performance_df["Gerçek Sıra"] = performance_df["% Değişim"].rank(ascending=False)

        # Gerçek performansa göre sırala
        performance_df = performance_df.sort_values("Gerçek Sıra")

        st.dataframe(performance_df)

        avg_perf = performance_df["% Değişim"].mean()

        if avg_perf > 0:
            st.success(f"Top7 Ortalama Performans: {avg_perf:.2f}%")
        else:
            st.error(f"Top7 Ortalama Performans: {avg_perf:.2f}%")

    else:
        st.warning("Ay başı verisi bulunamadı.")


    # ================================
    # 💰 LOT PLANI
    # ================================

    st.markdown("### 💰 Eşit Ağırlıklı Lot Planı")

    capital = st.number_input("Toplam Sermaye (TL)", value=100000)
    equal_weight = capital / 7

    latest_prices = close.iloc[-1][top7.index]

    lot_plan = pd.DataFrame()
    lot_plan["Fiyat"] = latest_prices
    lot_plan["Ayrılan Tutar"] = equal_weight
    lot_plan["Alınabilecek Lot"] = (equal_weight / latest_prices).astype(int)
    lot_plan["Kullanılan Tutar"] = lot_plan["Alınabilecek Lot"] * lot_plan["Fiyat"]

    st.dataframe(lot_plan)


# ==========================================================
# 📚 TAB 3 — BACKTEST
# ==========================================================

with tab3:

    st.markdown("## 📚 Momentum Backtest (2015-2026)")

    from universe import katilim_list

    data_bt = yf.download(katilim_list, start="2015-01-01")
    close_bt = data_bt["Close"].dropna(axis=1, how="all")
    close_bt = close_bt.dropna(axis=1, thresh=252)

    momentum_bt = close_bt.pct_change(60)
    momentum_monthly_bt = momentum_bt.resample("ME").last()

    prices_monthly_bt = close_bt.resample("ME").last()
    monthly_returns_bt = prices_monthly_bt.pct_change()

    signals_bt = (momentum_monthly_bt.rank(axis=1, ascending=False) <= 7).astype(int)
    signals_shifted_bt = signals_bt.shift(1)

    weights_bt = signals_shifted_bt.div(signals_shifted_bt.sum(axis=1), axis=0)
    weights_bt = weights_bt.fillna(0)

    portfolio_returns_bt = (weights_bt * monthly_returns_bt).sum(axis=1)
    portfolio_returns_bt = portfolio_returns_bt.dropna()

    equity_bt = (1 + portfolio_returns_bt).cumprod()

    years = len(equity_bt) / 12
    cagr_bt = equity_bt.iloc[-1] ** (1/years) - 1
    vol_bt = portfolio_returns_bt.std() * np.sqrt(12)
    sharpe_bt = cagr_bt / vol_bt

    peak_bt = equity_bt.cummax()
    dd_bt = equity_bt / peak_bt - 1
    max_dd_bt = dd_bt.min()

    st.write(f"Final Equity: {round(equity_bt.iloc[-1],2)}")
    st.write(f"CAGR: {round(cagr_bt,3)}")
    st.write(f"Sharpe: {round(sharpe_bt,3)}")
    st.write(f"Max DD: {round(max_dd_bt,3)}")

    st.line_chart(equity_bt)

