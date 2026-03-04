def run_system():

    import json
    from config import MAX_DRAWDOWN_LIMIT as MAX_DRAWDOWN
    import yfinance as yf
    import pandas as pd

    from config import MODE

    from portfolio_engine import load_cash, load_portfolio, calculate_equity
    from stop_engine import calculate_atr, update_trailing_stop, initial_stop
    from execution_engine import open_position, close_position, update_stop
    from universe import katilim_list
    from log_engine import write_log
    from telegram_engine import send_telegram


    print("\n" + "="*40)
    print("      KATILIM MOMENTUM SİSTEMİ")
    print("="*40)

    write_log("CORE ENGINE BAŞLADI")

    # --- RAPOR DOSYASINI OLUŞTUR / SIFIRLA ---
    with open("rebalance_report.txt", "w", encoding="utf-8") as f:
        f.write(f"REBALANCE RAPORU - {pd.Timestamp.today().date()}\n")
        f.write("-" * 40 + "\n")

    # 1️⃣ Cash ve portföy yükle
    cash = load_cash()
    portfolio = load_portfolio()

    print(f"NAKİT: {cash:.2f} TL")
    print("AÇIK POZİSYON SAYISI:", len(portfolio))

    # 2️⃣ Açık pozisyon varsa fiyatları çek
    market_prices = {}

    if not portfolio.empty:
        tickers = portfolio["Stock"].tolist()
        data = yf.download(tickers, period="5d")
        close_prices = data["Close"].iloc[-1]

        if isinstance(close_prices, pd.Series):
            market_prices = close_prices.to_dict()
        else:
            market_prices[tickers[0]] = float(close_prices)

    # 3️⃣ Equity hesapla
    equity = calculate_equity(market_prices)
    print(f"EQUITY: {equity:.2f} TL")

    # --- DRAWDOWN KONTROLÜ ---

    with open("risk_state.json", "r") as f:
        risk_data = json.load(f)

    # İlk çalıştırma için peak ayarla
    if risk_data["peak_equity"] == 0:
        risk_data["peak_equity"] = equity

    # Yeni peak oluştuysa güncelle
    if equity > risk_data["peak_equity"]:
        risk_data["peak_equity"] = equity

    # Drawdown hesapla
    drawdown = 1 - (equity / risk_data["peak_equity"])

    print(f"Drawdown: %{round(drawdown*100,2)}")

    # Freeze tetikle
    if drawdown > MAX_DRAWDOWN:
        risk_data["freeze"] = True
        print("🚨 MAX DRAWDOWN AŞILDI - SİSTEM FREEZE MODUNDA")
        send_telegram("🚨 MAX DRAWDOWN AŞILDI - SİSTEM DURDU")

    with open("risk_state.json", "w") as f:
        json.dump(risk_data, f)

    # 4️⃣ Trend kontrolü (BIST100 MA200)
    print("\nTREND KONTROLÜ")

    xu100 = yf.download("XU100.IS", period="400d")
    xu_close = xu100["Close"].squeeze()
    ma200 = xu_close.rolling(200).mean()

    current_price = xu_close.iloc[-1]
    current_ma200 = ma200.iloc[-1]

    trend_ok = current_price > current_ma200

    print(f"BIST100: {current_price:.2f}")
    print(f"MA200: {current_ma200:.2f}")
    print(f"TREND: {'POZİTİF' if trend_ok else 'NEGATİF'}")
    with open("rebalance_report.txt", "a", encoding="utf-8") as f:
        f.write(f"Trend: {'POZİTİF' if trend_ok else 'NEGATİF'}\n")
        f.write(f"Equity: {round(equity,2)} TL\n")
        f.write(f"Pozisyon Sayısı: {len(portfolio)}\n\n")

    today = pd.Timestamp.today().normalize()
    is_rebalance_day = today.day <= 3 and today.weekday() < 5

    # 5️⃣ Stop kontrolü
    if not portfolio.empty:
        print("\nSTOP KONTROLÜ")

        for _, row in portfolio.iterrows():

            stock = row["Stock"]

            if stock in market_prices:
                current_price = market_prices[stock]
                stop_price = float(row["Stop"])

                print(f"{stock} Güncel: {current_price:.2f} | Stop: {stop_price:.2f}")

                # STOP TETİKLENİRSE
                if current_price <= stop_price:

                    print(f"{stock} STOP TETİKLENDİ")

                    
                    close_position(stock, current_price)
                    send_telegram(f"🚨 STOP → {stock} | Fiyat: {current_price}")

                    if MODE == "SEMI":
                        with open("rebalance_report.txt", "a", encoding="utf-8") as f:
                            f.write(f"\nSTOP → {stock} | Fiyat: {current_price:.2f}")

                    write_log(f"STOP → {stock} {current_price} fiyattan kapatıldı.")

                else:
                    # Trailing stop güncelle
                    data_full = yf.download(stock, period="6mo")
                    atr_series = calculate_atr(data_full)

                    new_stop = update_trailing_stop(
                        stop_price,
                        row["EntryDate"],
                        data_full,
                        atr_series
                    )

                    if new_stop > stop_price:
                        update_stop(stock, new_stop)

    # Stop sonrası equity yeniden hesapla
    cash = load_cash()
    portfolio = load_portfolio()

    market_prices = {}
    if not portfolio.empty:
        tickers = portfolio["Stock"].tolist()
        data = yf.download(tickers, period="5d")
        close_prices = data["Close"].iloc[-1]

        if isinstance(close_prices, pd.Series):
            market_prices = close_prices.to_dict()
        else:
            market_prices[tickers[0]] = float(close_prices)

    equity = calculate_equity(market_prices)

    # 6️⃣ REBALANCE (Top7 Eşit Dağılım)
    if trend_ok and is_rebalance_day and not risk_data["freeze"]:

        # --- REBALANCE FLAG KONTROLÜ ---
        current_month = pd.Timestamp.today().strftime("%Y-%m")

        with open("rebalance_flag.json", "r") as f:
            flag_data = json.load(f)

        if flag_data["last_rebalance"] == current_month:
            print("Bu ay zaten rebalance yapılmış. Atlanıyor.")

        else:

            # --- PORTFÖYÜ RESETLE (ÖNCE HEPSİNİ SAT) ---
            if not portfolio.empty:

                print("Eski pozisyonlar kapatılıyor...")

                for _, row in portfolio.iterrows():

                    stock = row["Stock"]

                    if stock in market_prices:
                        current_price = market_prices[stock]

                        close_position(stock, current_price)

                        send_telegram(f"🔴 KAPAT → {stock} | Fiyat: {current_price}")

                        if MODE == "SEMI":
                            with open("rebalance_report.txt", "a", encoding="utf-8") as f:
                                f.write(f"\nKAPAT → {stock} | Fiyat: {current_price:.2f}")

                cash = load_cash()
                portfolio = load_portfolio()
                equity = cash

            print("\nREBALANCE BAŞLIYOR")

            # Top7 hesapla
            data = yf.download(katilim_list, period="90d")
            close = data["Close"]

            momentum_60 = close.pct_change(60, fill_method=None).iloc[-1]
            ranked = momentum_60.sort_values(ascending=False)

            top7 = ranked.head(7)

            # --- TOP7 DOSYAYA YAZ ---
            top7_df = pd.DataFrame({
            "Stock": top7.index,
            "Momentum": top7.values
            })

            top7_df.to_csv("top7_current.csv", index=False)

            print("Top 7:")
            print(top7)

            allocation = equity / 7

            for stock in top7.index:

                data_full = yf.download(stock, period="6mo")
                close_series = data_full["Close"].squeeze()
                entry_price = close_series.iloc[-1]

                atr_series = calculate_atr(data_full)
                atr_value = atr_series.iloc[-1]

                stop_price = initial_stop(entry_price, atr_value)

                lot = int(allocation / entry_price)

                if lot > 0:

                    open_position(
                        stock=stock,
                        entry_date=str(pd.Timestamp.today().date()),
                        entry_price=float(entry_price),
                        lot=lot,
                        stop_price=float(stop_price)
                    )

                    send_telegram(f"🟢 ALIM → {stock} | Lot: {lot} | Fiyat: {entry_price:.2f}")

                    if MODE == "SEMI":
                        with open("rebalance_report.txt", "a", encoding="utf-8") as f:
                            f.write(f"\nAL → {stock} | Lot: {lot} | Fiyat: {entry_price:.2f} | Stop: {stop_price:.2f}")

                    print(f"{stock} alındı | Lot: {lot}")
                    write_log(f"REBALANCE ALIM → {stock} {lot} lot {entry_price}")

            # --- FLAG GÜNCELLE ---
            flag_data["last_rebalance"] = current_month

            with open("rebalance_flag.json", "w") as f:
                json.dump(flag_data, f)

    else:
        print("\nRebalance yapılmadı (trend negatif veya rebalance günü değil).")

    # --- İşlem var mı kontrol et ---
    with open("rebalance_report.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) <= 6:
        with open("rebalance_report.txt", "a", encoding="utf-8") as f:
            f.write("Bugün işlem sinyali oluşmadı.\n")

    print("-" * 40)
    print("\nSİSTEM TAMAMLANDI")
    print("="*40)

    # Günlük log
    today_str = str(pd.Timestamp.today().date())

    
    # --- EQUITY HISTORY KAYDI ---

    import os

    if os.path.exists("equity_history.csv"):
        history_df = pd.read_csv("equity_history.csv")
    else:
        history_df = pd.DataFrame(columns=["Date","Equity","Cash","Positions"])

    today_str = str(pd.Timestamp.today().date())

    # Aynı gün tekrar yazmasın diye kontrol
    if today_str not in history_df["Date"].values:

        new_row = {
            "Date": today_str,
            "Equity": round(equity, 2),
            "Cash": round(cash, 2),
            "Positions": len(portfolio)
        }

        history_df = pd.concat([history_df, pd.DataFrame([new_row])])
        history_df.to_csv("equity_history.csv", index=False)

        print("Equity history kaydedildi.")
    # --- PERFORMANS HESAPLAMA ---

    import os

    if os.path.exists("equity_history.csv"):
        history_df = pd.read_csv("equity_history.csv")

        if len(history_df) > 1:
            history_df["Peak"] = history_df["Equity"].cummax()
            history_df["Drawdown"] = 1 - (history_df["Equity"] / history_df["Peak"])

    if len(history_df) > 1:

        history_df["Peak"] = history_df["Equity"].cummax()
        history_df["Drawdown"] = 1 - (history_df["Equity"] / history_df["Peak"])

        max_dd = history_df["Drawdown"].max()

        start_equity = history_df["Equity"].iloc[0]
        current_equity = history_df["Equity"].iloc[-1]

        total_return = (current_equity / start_equity) - 1

        days = len(history_df)
        cagr = (1 + total_return) ** (252 / days) - 1

    from report_engine import generate_daily_report

    report_message = generate_daily_report()

    print("DEBUG:", report_message)

    if report_message:
        send_telegram(report_message)

        from github_backup import upload_file

        upload_file("equity_history.csv")
        upload_file("performance_log.csv")
        upload_file("portfolio_state.csv")
 

    if __name__ == "__main__":
        run_system()



