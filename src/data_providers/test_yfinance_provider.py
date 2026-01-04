from src.data_providers.yfinance_provider import YFinanceProvider

provider = YFinanceProvider()
metrics = provider.get_core_metrics("NVDA")

print(metrics)
