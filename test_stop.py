import yfinance as yf
from stop_engine import calculate_atr, initial_stop, update_trailing_stop

# Veri çek
data = yf.download("ASELS.IS", period="6mo")

# ATR hesapla
atr = calculate_atr(data)

# 30 gün önce giriş yaptığımızı varsayalım
entry_index = data.index[-30]
entry_price = data["Close"].loc[entry_index]
atr_value = atr.loc[entry_index]

# İlk stop
current_stop = initial_stop(entry_price, atr_value)

print("GİRİŞ FİYATI:", entry_price)
print("İLK STOP:", round(current_stop, 2))

# Şimdi trailing test edelim (bugünkü veriye göre)
updated_stop = update_trailing_stop(
    current_stop,
    entry_index,
    data,
    atr
)

print("GÜNCEL STOP:", round(updated_stop, 2))
