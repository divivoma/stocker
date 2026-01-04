import yfinance as yf

tickers = {
    "Infineon": "IFX.DE",
    "NXP": "NXPI",
    "STMicro": "STM",
    "Texas Instruments": "TXN",
    "NVIDIA": "NVDA",
    "Ferrari": "RACE",
}

for name, symbol in tickers.items():
    print(f"\n=== {name} ({symbol}) ===")
    t = yf.Ticker(symbol)

    info = t.info
    qf = t.quarterly_financials

    print("Price:", info.get("currentPrice"))
    print("Market Cap:", info.get("marketCap"))
    print("PE TTM:", info.get("trailingPE"))
    print("PE Forward:", info.get("forwardPE"))
    print("Gross Margin:", info.get("grossMargins"))

    if "Net Income" in qf.index:
        print("Latest Quarter Net Income:", qf.loc["Net Income"].iloc[0])
    else:
        print("Net Income: NOT AVAILABLE")

