"""
Test Google News RSS dla polskich spółek.
Nie wymaga żadnego API key — działa od razu.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

queries = [
    ("PKO BP akcje", "PKO.WA"),
    ("KGHM giełda", "KGH.WA"),
    ("CD Projekt wyniki", "CDR.WA"),
    ("Orlen akcje GPW", "PKN.WA"),
]

for query, ticker in queries:
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=pl&gl=PL&ceid=PL:pl"
    
    print(f"\n=== {ticker}: {query} ===")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")
        print(f"Liczba artykułów: {len(items)}")
        for item in items[:3]:
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
            source = item.find("source").get_text(strip=True) if item.find("source") else ""
            print(f"  [{date[:16]}] {source}: {title[:70]}")
    except Exception as e:
        print(f"BŁĄD: {e}")