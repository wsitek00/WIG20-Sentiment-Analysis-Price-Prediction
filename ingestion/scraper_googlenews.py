"""
Pobieranie newsów przez Google News RSS.
Brak API key, 100+ artykułów per spółka, wiele polskich źródeł.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import yaml
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from loguru import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _build_query(ticker_info: dict) -> str:
    """Buduje zapytanie dla Google News na podstawie słów kluczowych spółki."""
    keywords = ticker_info["keywords"]
    # Użyj pierwszego słowa kluczowego + kontekst giełdowy
    main_kw = keywords[0]
    return f"{main_kw} akcje GPW wyniki"


def scrape_google_news_ticker(ticker_info: dict, days_back: int = 90) -> list:
    """Pobiera newsy dla jednej spółki z Google News RSS."""
    query = _build_query(ticker_info)
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=pl&gl=PL&ceid=PL:pl"
    cutoff = datetime.now() - timedelta(days=days_back)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Błąd {ticker_info['symbol']}: {e}")
        return []

    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")

    articles = []
    for item in items:
        title_tag = item.find("title")
        link_tag = item.find("link")
        date_tag = item.find("pubDate")
        source_tag = item.find("source")

        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        url_art = link_tag.get_text(strip=True) if link_tag else ""
        source = source_tag.get_text(strip=True) if source_tag else "unknown"

        published_at = None
        if date_tag:
            try:
                published_at = parsedate_to_datetime(date_tag.get_text(strip=True))
                if published_at.replace(tzinfo=None) < cutoff:
                    continue
            except Exception:
                pass

        articles.append({
            "title": title,
            "url": url_art,
            "published_at": published_at.isoformat() if published_at else None,
            "source": source,
            "ticker_mentioned": ticker_info["symbol"],
            "scraped_at": datetime.now().isoformat()
        })

    return articles


def scrape_google_news(days_back: int = 90, config_path: str = "config.yaml") -> pd.DataFrame:
    """Pobiera newsy dla wszystkich spółek WIG20 z Google News."""
    config = load_config(config_path)
    tickers = config["tickers"]
    delay = config["ingestion"]["request_delay"]

    all_articles = []
    for ticker_info in tickers:
        symbol = ticker_info["symbol"]
        articles = scrape_google_news_ticker(ticker_info, days_back=days_back)
        all_articles.extend(articles)
        logger.info(f"  {symbol}: {len(articles)} newsów")
        time.sleep(delay)

    df = pd.DataFrame(all_articles)
    if not df.empty:
        df.drop_duplicates(subset=["title", "ticker_mentioned"], inplace=True)

    logger.success(f"Google News: zebrano {len(df)} artykułów łącznie.")
    return df


if __name__ == "__main__":
    df = scrape_google_news(days_back=90)
    if not df.empty:
        print(df[["title", "published_at", "ticker_mentioned", "source"]].head(15).to_string())
        print(f"\nPer spółka:\n{df['ticker_mentioned'].value_counts().to_string()}")
        print(f"\nNajczęstsze źródła:\n{df['source'].value_counts().head(10).to_string()}")
    else:
        print("Brak artykułów.")