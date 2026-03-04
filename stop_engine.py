import pandas as pd
import numpy as np

def calculate_atr(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    return atr


def initial_stop(entry_price, atr_value, multiplier=2.5):
    return entry_price - (atr_value * multiplier)


def update_trailing_stop(current_stop, entry_index, df, atr_series, multiplier=2.5):

    import pandas as pd

    # Eğer veri boşsa stop değiştirme
    if df is None or df.empty:
        return current_stop

    close_series = df["Close"].squeeze()

    # Close serisi boşsa
    if close_series.empty:
        return current_stop

    # Entry date datetime'a çevir
    entry_index = pd.to_datetime(entry_index)

    # Entry'den sonraki veriyi al
    close_series = close_series.loc[entry_index:]

    # Eğer entry sonrası veri yoksa
    if close_series.empty:
        return current_stop

    # ATR boşsa
    if atr_series is None or atr_series.empty:
        return current_stop

    latest_close = close_series.iloc[-1]
    latest_atr = float(atr_series.iloc[-1])

    new_stop = latest_close - (latest_atr * multiplier)

    return max(current_stop, new_stop)


