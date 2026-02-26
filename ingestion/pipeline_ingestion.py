"""
Orkiestrator modułu Ingestion.
Uruchamia wszystkie scrapery i łączy dane w jeden plik.
"""
import pandas as pd
import os
import yaml
from loguru import logger
from ingestion.scraper_bankier import scrape_bankier
from ingestion.fetcher_yfinance import fetch_prices, save_prices


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_ingestion(days: int = 90, config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    os.makedirs("data/raw", exist_ok=True)

    # --- 1. Pobierz ceny ---
    logger.info("Pobieranie cen spółek WIG20...")
    prices_df = fetch_prices(days=days, config_path=config_path)
    save_prices(prices_df, config["paths"]["raw_prices"])

    # --- 2. Pobierz newsy ---
    all_news = []

    if config["sources"]["bankier"]["enabled"]:
        logger.info("Scraping: Bankier.pl...")
        bankier_df = scrape_bankier(max_pages=10, config_path=config_path)
        all_news.append(bankier_df)

    # Tutaj możesz dodać kolejne scrapery:
    # if config["sources"]["money"]["enabled"]:
    #     from ingestion.scraper_money import scrape_money
    #     all_news.append(scrape_money(...))

    if all_news:
        news_df = pd.concat(all_news, ignore_index=True)
        news_df.drop_duplicates(subset=["title", "source"], inplace=True)
        news_df.to_csv(config["paths"]["raw_news"], index=False)
        logger.success(f"Zapisano {len(news_df)} artykułów do {config['paths']['raw_news']}")
    else:
        logger.warning("Brak artykułów do zapisania.")


if __name__ == "__main__":
    run_ingestion(days=90)
