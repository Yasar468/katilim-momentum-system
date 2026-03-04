import pandas as pd

def load_cash():
    df = pd.read_csv("cash_state.csv")
    return float(df["Cash"].iloc[0])


def load_portfolio():
    df = pd.read_csv("portfolio_state.csv")
    return df


def calculate_equity(market_prices):

    cash = load_cash()
    portfolio = load_portfolio()

    position_value = 0

    for _, row in portfolio.iterrows():
        stock = row["Stock"]
        lot = row["Lot"]

        if stock in market_prices:
            price = market_prices[stock]
            position_value += lot * price

    equity = cash + position_value

    return equity
