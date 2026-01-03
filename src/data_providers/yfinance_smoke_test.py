import yfinance as yf

ticker = yf.Ticker("AAPL")

info = ticker.info
financials = ticker.financials
quarterly_financials = ticker.quarterly_financials

print("PRICE:", info.get("currentPrice"))
print("MARKET CAP:", info.get("marketCap"))
print("PE TTM:", info.get("trailingPE"))
print("PE FORWARD:", info.get("forwardPE"))
print("GROSS MARGIN:", info.get("grossMargins"))

print("\nLATEST QUARTER NET INCOME:")
if "Net Income" in quarterly_financials.index:
    print(quarterly_financials.loc["Net Income"].iloc[0])
else:
    print("Net Income not available")

print("\nLAST 4 QUARTERS NET INCOME:")
if "Net Income" in quarterly_financials.index:
    print(quarterly_financials.loc["Net Income"].head(4))
else:
    print("Net Income not available")
