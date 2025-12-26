from src.market_data import collect_market_data
from src.news import collect_news
from src.excel_writer import write_report
from src.utils import get_logger


def main():
    logger = get_logger()
    logger.info("Weekly stock tracker started")

    market_df = collect_market_data()
    news_df = collect_news()

    write_report(market_df, news_df)

    logger.info("Weekly stock tracker completed")

if __name__ == "__main__":
    main()

