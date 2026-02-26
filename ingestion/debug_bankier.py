"""
Skrypt diagnostyczny — sprawdza strukturę HTML Bankier.pl
Uruchom i wklej output do Claude.
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

url = "https://www.bankier.pl/gielda/wiadomosci-gieldowe/wszystkie"
response = requests.get(url, headers=HEADERS, timeout=10)
soup = BeautifulSoup(response.text, "lxml")

print("=== SZUKAM TAGÓW Z ARTYKUŁAMI ===\n")

# Sprawdź różne możliwe selektory
tests = [
    ("article", {}),
    ("div", {"class": "entry"}),
    ("div", {"class": "row"}),
    ("li", {"class": "article"}),
    ("a", {"class": lambda c: c and "article" in str(c)}),
]

for tag, attrs in tests:
    items = soup.find_all(tag, attrs if attrs else True)
    if items:
        print(f"soup.find_all('{tag}', {attrs}) → {len(items)} elementów")

print("\n=== PIERWSZE 3 LINKI Z TYTUŁAMI ===\n")
# Pokaż wszystkie linki które wyglądają jak artykuły
links = soup.find_all("a", href=True)
news_links = [a for a in links if "/wiadomosci/" in a.get("href", "") or "/gielda/" in a.get("href", "")]
for a in news_links[:10]:
    print(f"  TEXT: {a.get_text(strip=True)[:80]}")
    print(f"  HREF: {a['href']}")
    print(f"  PARENT TAG: <{a.parent.name} class='{a.parent.get('class', '')}'>")
    print()

print("\n=== FRAGMENT HTML (pierwsze 3000 znaków body) ===\n")
body = soup.find("body")
if body:
    print(str(body)[:3000])