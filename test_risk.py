from risk_engine import calculate_position_size

equity = 11727.41
cash = 11727.41
entry_price = 300
stop_price = 260

lot = calculate_position_size(equity, cash, entry_price, stop_price)

print("HESAPLANAN LOT:", lot)
