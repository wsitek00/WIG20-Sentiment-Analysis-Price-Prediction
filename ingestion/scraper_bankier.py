"""
Scraper nagłówków newsów z Bankier.pl
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import yaml
from datetime import datetime
from loguru import logger


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def scrape_bankier(max_pages: int = 10, config_path: str = "config.yaml") -> pd.DataFrame:
    """
    Scrape nagłówków z Bankier.pl — sekcja wiadomości giełdowych.

    Returns:
        DataFrame z kolumnami: title, url, published_at, source, ticker_mentioned
    """
    config = load_config(config_path)
    base_url = config["sources"]["bankier"]["base_url"]
    news_url = config["sources"]["bankier"]["news_url"]
    delay = config["ingestion"]["request_delay"]
    tickers = config["tickers"]

    articles = []

    for page in range(1, max_pages + 1):
        url = f"{news_url}?page={page}" if page > 1 else news_url
        logger.info(f"Bankier.pl — strona {page}: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Błąd przy pobieraniu strony {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "lxml")

        # Bankier.pl — artykuły są w tagach <article> lub <div class="...">
        # Struktura może się zmieniać — sprawdź w DevTools przeglądarki
        news_items = soup.find_all("article", class_=lambda c: c and "article" in c.lower())

        if not news_items:
            # Alternatywny selektor
            news_items = soup.select("div.C_NL-Item-Article, div.news-item, li.article")

        if not news_items:
            logger.warning(f"Brak artykułów na stronie {page} — możliwa zmiana struktury HTML.")
            break

        for item in news_items:
            title_tag = item.find("a") or item.find("h2") or item.find("h3")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link and not link.startswith("http"):
                link = base_url + link

            # Znajdź datę publikacji
            date_tag = item.find("time") or item.find(class_=lambda c: c and "date" in str(c).lower())
            published_at = None
            if date_tag:
                published_at = date_tag.get("datetime") or date_tag.get_text(strip=True)

            # Sprawdź, której spółki dotyczy artykuł
            ticker_mentioned = _find_mentioned_ticker(title, tickers)

            articles.append({
                "title": title,
                "url": link,
                "published_at": published_at,
                "source": "bankier",
                "ticker_mentioned": ticker_mentioned,
                "scraped_at": datetime.now().isoformat()
            })

        time.sleep(delay)  # Szanuj serwer!

    df = pd.DataFrame(articles)
    logger.success(f"Bankier.pl: zebrano {len(df)} artykułów.")
    return df


def _find_mentioned_ticker(title: str, tickers: list) -> str | None:
    """Sprawdza, czy tytuł artykułu zawiera słowo kluczowe którejś spółki."""
    title_lower = title.lower()
    for ticker_info in tickers:
        for keyword in ticker_info["keywords"]:
            if keyword.lower() in title_lower:
                return ticker_info["symbol"]
    return None  # Artykuł ogólny (makro, rynek)


if __name__ == "__main__":
    df = scrape_bankier(max_pages=3)
    print(df.head())
    print(f"\nSpółki wymienione:\n{df['ticker_mentioned'].value_counts()}")
