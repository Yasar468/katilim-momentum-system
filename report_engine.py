import pandas as pd
import numpy as np
from datetime import datetime

def generate_daily_report():

    try:
        df = pd.read_csv("equity_history.csv")
    except:
        return None

    if len(df) < 2:
        return None

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    df["Daily_Return"] = df["Equity"].pct_change()

    today_equity = df["Equity"].iloc[-1]
    daily_return = df["Daily_Return"].iloc[-1]

    peak = df["Equity"].cummax()
    drawdown_series = 1 - (df["Equity"] / peak)

    current_drawdown = drawdown_series.iloc[-1]
    max_dd = drawdown_series.max()

    start_equity = df["Equity"].iloc[0]
    total_return = (today_equity / start_equity) - 1

    report_row = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Equity": today_equity,
        "Daily_Return": daily_return,
        "Drawdown": current_drawdown
    }

    try:
        log_df = pd.read_csv("performance_log.csv")
        log_df = pd.concat([log_df, pd.DataFrame([report_row])])
    except:
        log_df = pd.DataFrame([report_row])

    log_df.to_csv("performance_log.csv", index=False)

    message = (
        f"📊 KATILIM MOMENTUM – GÜNLÜK RAPOR\n"
        f"Tarih: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"💰 Equity: {today_equity:,.2f} TL\n"
        f"📈 Günlük Getiri: %{daily_return*100:.2f}\n"
        f"📉 Max DD: %{max_dd*100:.2f}\n\n"
        f"📊 Toplam Getiri: %{total_return*100:.2f}\n"
        f"📆 İşlem Günü: {len(df)}"
    )

    return message