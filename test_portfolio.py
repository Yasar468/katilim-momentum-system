from portfolio_engine import load_cash, load_portfolio, calculate_equity

# Şu an portföy boş olduğu için
# market_prices boş dictionary olabilir
market_prices = {}

cash = load_cash()
portfolio = load_portfolio()
equity = calculate_equity(market_prices)

print("NAKİT:", cash)
print("PORTFÖY:")
print(portfolio)
print("EQUITY:", equity)
