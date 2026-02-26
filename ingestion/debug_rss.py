"""
Test RSS feedów Bankier.pl — uruchom i wklej output.
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

feeds = [
    "https://www.bankier.pl/rss/wiadomosci.xml",
    "https://www.bankier.pl/rss/gielda.xml",
    "https://www.bankier.pl/rss/akcje.xml",
]

for url in feeds:
    print(f"\n=== {url} ===")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")
        print(f"Liczba artykułów: {len(items)}")
        for item in items[:3]:
            print(f"  TYTUŁ: {item.find('title').get_text()[:80]}")
            print(f"  DATA:  {item.find('pubDate').get_text() if item.find('pubDate') else 'brak'}")
            print()
    except Exception as e:
        print(f"BŁĄD: {e}")