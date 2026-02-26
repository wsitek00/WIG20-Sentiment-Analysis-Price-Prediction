"""
Pobieranie newsów z Bankier.pl przez RSS feed.
RSS jest niezawodny, daje czyste dane z datą — lepszy niż scraping HTML.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import yaml
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from loguru import logger


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

RSS_FEEDS = [
    "https://www.bankier.pl/rss/wiadomosci.xml",
    "https://www.bankier.pl/rss/gielda.xml",
]


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def scrape_bankier(days_back: int = 90, config_path: str = "config.yaml") -> pd.DataFrame:
    """
    Pobiera newsy z Bankier.pl przez RSS.

    Returns:
        DataFrame: title, url, published_at, source, ticker_mentioned
    """
    config = load_config(config_path)
    tickers = config["tickers"]
    cutoff_date = datetime.now() - timedelta(days=days_back)

    articles = []

    for feed_url in RSS_FEEDS:
        logger.info(f"Pobieranie RSS: {feed_url}")
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Błąd RSS {feed_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "xml")
        items = soup.find_all("item")
        logger.info(f"  Znaleziono {len(items)} artykułów")

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            date_tag = item.find("pubDate")

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            url = link_tag.get_text(strip=True) if link_tag else ""

            # Parsuj datę z formatu RFC 2822 (standard RSS)
            published_at = None
            if date_tag:
                try:
                    published_at = parsedate_to_datetime(date_tag.get_text(strip=True))
                    # Pomiń artykuły starsze niż cutoff
                    if published_at.replace(tzinfo=None) < cutoff_date:
                        continue
                except Exception:
                    published_at = None

            ticker_mentioned = _find_mentioned_ticker(title, tickers)

            articles.append({
                "title": title,
                "url": url,
                "published_at": published_at.isoformat() if published_at else None,
                "source": "bankier",
                "ticker_mentioned": ticker_mentioned,
                "scraped_at": datetime.now().isoformat()
            })

        time.sleep(1)

    df = pd.DataFrame(articles)
    if not df.empty:
        df.drop_duplicates(subset=["title"], inplace=True)

    logger.success(f"Bankier.pl RSS: zebrano {len(df)} artykułów.")
    return df


def _find_mentioned_ticker(title: str, tickers: list) -> str | None:
    """Sprawdza, czy tytuł artykułu zawiera słowo kluczowe którejś spółki."""
    title_lower = title.lower()
    for ticker_info in tickers:
        for keyword in ticker_info["keywords"]:
            if keyword.lower() in title_lower:
                return ticker_info["symbol"]
    return None  # Artykuł ogólny (makro, rynek) — też wartościowy!


if __name__ == "__main__":
    df = scrape_bankier(days_back=90)
    print(df[["title", "published_at", "ticker_mentioned"]].to_string())
    print(f"\nSpółki wymienione:\n{df['ticker_mentioned'].value_counts(dropna=False)}")