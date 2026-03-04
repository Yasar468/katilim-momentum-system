def calculate_position_size(equity, cash, entry_price, stop_price, 
                            risk_pct=0.0175, commission_rate=0.001):

    # Trade başına risk
    risk_amount = equity * risk_pct

    stop_distance = entry_price - stop_price

    if stop_distance <= 0:
        return 0

    # Risk bazlı lot
    risk_lot = risk_amount / stop_distance

    # Nakit bazlı maksimum lot (komisyon dahil)
    effective_price = entry_price * (1 + commission_rate)
    cash_lot = cash / effective_price

    final_lot = int(min(risk_lot, cash_lot))

    return final_lot

