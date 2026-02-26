"""
Orkiestrator modułu Ingestion.
Źródła: Bankier.pl (RSS, bieżące) + Stooq.pl (historia per spółka)
"""
import pandas as pd
import os
import yaml
from loguru import logger
from ingestion.scraper_bankier import scrape_bankier
from ingestion.scraper_stooq import scrape_stooq
from ingestion.fetcher_yfinance import fetch_prices, save_prices


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_ingestion(days: int = 90, config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    os.makedirs("data/raw", exist_ok=True)

    # 1. Ceny
    logger.info("Pobieranie cen spółek WIG20...")
    prices_df = fetch_prices(days=days, config_path=config_path)
    save_prices(prices_df, config["paths"]["raw_prices"])

    # 2. Newsy — Bankier RSS (bieżące)
    logger.info("Scraping: Bankier.pl RSS...")
    bankier_df = scrape_bankier(days_back=days, config_path=config_path)

    # 3. Newsy — Stooq (historia per spółka)
    logger.info("Scraping: Stooq.pl...")
    stooq_df = scrape_stooq(days_back=days, config_path=config_path)

    # 4. Połącz i zapisz
    all_news = pd.concat([bankier_df, stooq_df], ignore_index=True)
    all_news.drop_duplicates(subset=["title", "source"], inplace=True)
    all_news.to_csv(config["paths"]["raw_news"], index=False)

    logger.success(f"Zapisano {len(all_news)} artykułów do {config['paths']['raw_news']}")
    logger.info(f"Per spółka:\n{all_news['ticker_mentioned'].value_counts(dropna=False).to_string()}")


if __name__ == "__main__":
    run_ingestion(days=90)