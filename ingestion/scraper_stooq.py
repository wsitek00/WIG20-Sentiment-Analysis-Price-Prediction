"""
Pobieranie newsów ze Stooq.pl — archiwa per spółka.
Stooq ma historyczne newsy dla każdego tickera GPW, idealne do analizy.
URL pattern: https://stooq.pl/n/?s=pko
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import yaml
from datetime import datetime, timedelta
from loguru import logger


HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Mapowanie ticker GPW → symbol Stooq (małe litery bez .WA)
STOOQ_SYMBOLS = {
    "PKN.WA": "pkn",
    "PKO.WA": "pko",
    "PZU.WA": "pzu",
    "KGH.WA": "kgh",
    "LPP.WA": "lpp",
    "CDR.WA": "cdr",
    "ALE.WA": "ale",
    "MBK.WA": "mbk",
    "DNP.WA": "dnp",
    "CPS.WA": "cps",
}


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def scrape_stooq_ticker(symbol_gpw: str, symbol_stooq: str, days_back: int = 90) -> list:
    """Pobiera newsy dla jednej spółki ze Stooq.pl."""
    url = f"https://stooq.pl/n/?s={symbol_stooq}"
    cutoff = datetime.now() - timedelta(days=days_back)
    articles = []

    logger.info(f"  Stooq: {symbol_gpw} → {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"  Błąd {symbol_gpw}: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")

    # Stooq: newsy są w tabeli lub liście — szukamy linków z datami
    rows = soup.select("table tr") or soup.select("div.news li")

    for row in rows:
        link_tag = row.find("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        if href and not href.startswith("http"):
            href = "https://stooq.pl" + href

        # Znajdź datę w wierszu
        date_text = row.get_text(strip=True).replace(title, "").strip()
        published_at = None
        try:
            # Stooq format: "2026-02-26" lub "26.02.2026"
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    published_at = datetime.strptime(date_text[:10], fmt)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

        if published_at and published_at < cutoff:
            continue

        if title and len(title) > 10:
            articles.append({
                "title": title,
                "url": href,
                "published_at": published_at.isoformat() if published_at else None,
                "source": "stooq",
                "ticker_mentioned": symbol_gpw,
                "scraped_at": datetime.now().isoformat()
            })

    return articles


def scrape_stooq(days_back: int = 90, config_path: str = "config.yaml") -> pd.DataFrame:
    """Pobiera newsy dla wszystkich spółek WIG20 ze Stooq.pl."""
    config = load_config(config_path)
    delay = config["ingestion"]["request_delay"]

    all_articles = []
    for gpw_symbol, stooq_symbol in STOOQ_SYMBOLS.items():
        articles = scrape_stooq_ticker(gpw_symbol, stooq_symbol, days_back)
        all_articles.extend(articles)
        logger.info(f"  {gpw_symbol}: {len(articles)} newsów")
        time.sleep(delay)

    df = pd.DataFrame(all_articles)
    if not df.empty:
        df.drop_duplicates(subset=["title", "ticker_mentioned"], inplace=True)

    logger.success(f"Stooq.pl: zebrano {len(df)} artykułów łącznie.")
    return df


if __name__ == "__main__":
    df = scrape_stooq(days_back=90)
    print(df[["title", "published_at", "ticker_mentioned"]].head(20).to_string())
    print(f"\nPer spółka:\n{df['ticker_mentioned'].value_counts()}")