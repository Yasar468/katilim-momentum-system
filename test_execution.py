from execution_engine import open_position, close_position
from portfolio_engine import load_cash
import datetime

# Başlangıç nakdi göster
print("BAŞLANGIÇ NAKİT:", load_cash())

# Sahte pozisyon aç
open_position(
    stock="ASELS.IS",
    entry_date=str(datetime.date.today()),
    entry_price=300,
    lot=5,
    stop_price=260
)

print("POZİSYON AÇILDIKTAN SONRA NAKİT:", load_cash())

# Sahte pozisyon kapat (karla kapatalım)
#close_position(
#    stock="ASELS.IS",
#   exit_price=320
#)

#print("POZİSYON KAPANDIKTAN SONRA NAKİT:", load_cash())
