import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

r = requests.get("https://stooq.pl/n/?s=pko", headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, "lxml")

# Pokaż wszystkie tabele
tables = soup.find_all("table")
print(f"Liczba tabel: {len(tables)}")
for i, t in enumerate(tables[:3]):
    print(f"\n--- Tabela {i} ---")
    print(str(t)[:500])

# Pokaż linki wyglądające jak newsy
print("\n--- Linki z /n/ ---")
for a in soup.find_all("a", href=True):
    if "/n/" in a["href"]:
        print(f"  {a.get_text(strip=True)[:60]} → {a['href']}")