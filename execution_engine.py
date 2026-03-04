import pandas as pd

from config import COMMISSION_RATE, SLIPPAGE_RATE


def open_position(stock, entry_date, entry_price, lot, stop_price):

    # Cash'i yükle
    cash_df = pd.read_csv("cash_state.csv")
    cash = float(cash_df["Cash"].iloc[0])

    # Gerçek maliyet (komisyon dahil)
    # Slippage ekle (alışta fiyat yukarı kayar)
    fill_price = entry_price * (1 + SLIPPAGE_RATE)
    total_cost = lot * fill_price * (1 + COMMISSION_RATE)

    if total_cost > cash:
        print("Yetersiz nakit.")
        return False

    # Cash güncelle
    new_cash = cash - total_cost
    cash_df["Cash"] = new_cash
    cash_df.to_csv("cash_state.csv", index=False)

    # Portfolio güncelle
    portfolio_df = pd.read_csv("portfolio_state.csv")

    new_row = {
        "Stock": stock,
        "EntryDate": entry_date,
        "EntryPrice": fill_price,
        "Lot": lot,
        "Stop": stop_price
    }

    portfolio_df = pd.concat([portfolio_df, pd.DataFrame([new_row])])
    portfolio_df.to_csv("portfolio_state.csv", index=False)

    print(f"{stock} pozisyonu açıldı.")
    return True


def close_position(stock, exit_price):

    portfolio_df = pd.read_csv("portfolio_state.csv")
    cash_df = pd.read_csv("cash_state.csv")

    position = portfolio_df[portfolio_df["Stock"] == stock]

    if position.empty:
        print("Pozisyon bulunamadı.")
        return False

    lot = float(position["Lot"].iloc[0])

    # Net satış (komisyon dahil)
    # Slippage ekle (satışta fiyat aşağı kayar)
    fill_price = exit_price * (1 - SLIPPAGE_RATE)
    total_return = lot * fill_price * (1 - COMMISSION_RATE)

    # Cash güncelle
    cash = float(cash_df["Cash"].iloc[0])
    new_cash = cash + total_return
    cash_df["Cash"] = new_cash
    cash_df.to_csv("cash_state.csv", index=False)

    # Portföyden sil
    portfolio_df = portfolio_df[portfolio_df["Stock"] != stock]
    portfolio_df.to_csv("portfolio_state.csv", index=False)

    print(f"{stock} pozisyonu kapatıldı.")
    return True

def update_stop(stock, new_stop):

    portfolio_df = pd.read_csv("portfolio_state.csv")

    portfolio_df["Stop"] = portfolio_df["Stop"].astype(float)
    portfolio_df.loc[portfolio_df["Stock"] == stock, "Stop"] = float(new_stop)


    portfolio_df.to_csv("portfolio_state.csv", index=False)

    print(f"{stock} için yeni stop güncellendi: {new_stop:.2f}")
