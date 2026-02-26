# 📈 WIG20 Sentiment Analysis & Price Prediction

> **Projekt portfolio** — analiza wpływu sentymentu medialnego na notowania spółek WIG20  
> *Informatyka i Ekonometria | Python · NLP · Ekonometria*

---

## 🎯 Cel Projektu

System automatycznie pobiera nagłówki newsów z polskich portali finansowych, przetwarza je modelem NLP (FinBERT), a następnie bada statystyczną zależność między sentymentem medialnym a zmianami cen akcji spółek z indeksu WIG20.

**Hipoteza badawcza:** *Czy negatywny sentyment w polskich mediach finansowych poprzedza (w sensie Grangera) spadki cen spółek WIG20 z opóźnieniem 24–48h?*

---

## 🏗️ Architektura Systemu

```
wig20-sentiment/
│
├── 📁 ingestion/                  # Moduł 1: Pobieranie danych
│   ├── scraper_bankier.py         # Scraper nagłówków — Bankier.pl
│   ├── scraper_money.py           # Scraper nagłówków — Money.pl
│   ├── scraper_stockwatch.py      # Scraper — StockWatch.pl
│   ├── fetcher_yfinance.py        # Pobieranie cen WIG20 (yfinance)
│   └── pipeline_ingestion.py     # Orkiestrator — uruchamia wszystkie scrapery
│
├── 📁 processing/                 # Moduł 2: NLP i przetwarzanie
│   ├── sentiment_vader.py         # Baseline: VADER (szybki, prosty)
│   ├── sentiment_finbert.py       # Główny model: FinBERT (HuggingFace)
│   ├── aggregator.py              # Agregacja sentymentu → dzienna liczba
│   └── preprocessor.py           # Czyszczenie tekstu, tokenizacja
│
├── 📁 econometrics/               # Moduł 3: Analiza ekonometryczna
│   ├── granger_causality.py       # Test przyczynowości Grangera
│   ├── lag_analysis.py            # Analiza opóźnień (2h, 6h, 24h, 48h)
│   ├── ols_model.py               # Regresja OLS: cena ~ sentiment_lag
│   └── arimax_model.py            # Model ARIMAX z sentymentem jako egzogeną
│
├── 📁 visualization/              # Moduł 4: Wykresy i raport
│   ├── dashboard.py               # Interaktywny dashboard (Plotly/Dash)
│   ├── plot_correlation.py        # Wykresy korelacji cena-sentyment
│   └── report_generator.py       # Automatyczny raport PDF
│
├── 📁 data/
│   ├── raw/                       # Surowe dane (gitignore)
│   │   ├── news_raw.csv
│   │   └── prices_raw.csv
│   └── processed/                 # Dane po przetworzeniu
│       ├── sentiment_daily.csv    # Dzienny sentyment per spółka
│       └── merged_dataset.csv     # Ceny + sentyment (gotowe do modeli)
│
├── 📁 notebooks/                  # Eksploracja i prezentacja wyników
│   ├── 01_EDA.ipynb               # Eksploracyjna analiza danych
│   ├── 02_NLP_Analysis.ipynb      # Porównanie VADER vs FinBERT
│   └── 03_Econometrics.ipynb      # Wyniki testów i modeli
│
├── 📁 tests/                      # Testy jednostkowe
│   ├── test_scrapers.py
│   ├── test_sentiment.py
│   └── test_econometrics.py
│
├── config.yaml                    # Konfiguracja: spółki, daty, parametry
├── requirements.txt               # Zależności
├── .env.example                   # Szablon zmiennych środowiskowych
├── main.py                        # Punkt wejścia — uruchomienie całego pipeline
└── README.md
```

---

## 🔧 Stack Technologiczny

| Warstwa | Technologia | Zastosowanie |
|---|---|---|
| **Ingestion** | `BeautifulSoup`, `requests`, `yfinance` | Scraping newsów, pobieranie cen |
| **NLP** | `transformers` (FinBERT), `vaderSentiment` | Analiza sentymentu |
| **Przetwarzanie** | `pandas`, `numpy` | Czyszczenie, agregacja danych |
| **Ekonometria** | `statsmodels`, `scipy` | Granger, OLS, ARIMAX |
| **Wizualizacja** | `plotly`, `dash`, `matplotlib` | Dashboard, wykresy |
| **Środowisko** | `python-dotenv`, `loguru`, `pytest` | Konfiguracja, logi, testy |

---

## 📊 Przepływ Danych (Pipeline)

```
[Bankier.pl / Money.pl]          [GPW / yfinance]
        │                               │
        ▼                               ▼
  scraper_*.py                  fetcher_yfinance.py
        │                               │
        └──────────┬────────────────────┘
                   ▼
          preprocessor.py
         (czyszczenie tekstu)
                   │
                   ▼
          sentiment_finbert.py
         (sentyment per nagłówek)
                   │
                   ▼
            aggregator.py
      (dzienny sentyment per spółka)
                   │
                   ▼
          merged_dataset.csv
     (ceny + sentyment + lagi)
                   │
          ┌────────┴────────┐
          ▼                 ▼
   granger_causality    arimax_model
   lag_analysis         ols_model
          │                 │
          └────────┬────────┘
                   ▼
             dashboard.py
          (wyniki + wizualizacje)
```

---

## 🚀 Uruchomienie

### Instalacja
```bash
git clone https://github.com/twoj-nick/wig20-sentiment.git
cd wig20-sentiment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Konfiguracja
```bash
cp .env.example .env
# Edytuj .env — na razie nie są wymagane żadne klucze API
```

### Uruchomienie pełnego pipeline
```bash
# Pobierz dane z ostatnich 30 dni
python main.py --mode full --days 30

# Tylko scraping newsów
python main.py --mode ingest

# Tylko analiza sentymentu (na istniejących danych)
python main.py --mode sentiment

# Uruchom dashboard
python main.py --mode dashboard
```

---

## 📐 Metodologia Ekonometryczna

### 1. Test Przyczynowości Grangera
Sprawdzamy, czy sentyment *poprzedza* zmiany cen (a nie tylko z nimi koreluje):
```
H₀: sentyment NIE pomaga prognozować cen (nie jest przyczyną w sensie Grangera)
H₁: sentyment POMAGA prognozować ceny (jest przyczyną w sensie Grangera)
```
Testujemy dla opóźnień: 1, 2, 3, 5, 10 dni sesyjnych.

### 2. Analiza Opóźnień (Lag Analysis)
Szukamy optymalnego okna czasowego: przy którym opóźnieniu sentyment najsilniej koreluje ze zmianą ceny (korelacja Pearsona i Spearmana).

### 3. Model ARIMAX
```
ΔCena_t = α + β₁·ΔCena_{t-1} + β₂·Sentyment_{t-k} + ε_t
```
Gdzie `k` to optymalne opóźnienie znalezione w kroku 2.

---

## 🏢 Monitorowane Spółki WIG20

Projekt domyślnie śledzi 10 największych spółek z WIG20:

| Ticker GPW | Spółka | Sektor |
|---|---|---|
| PKN | PKN Orlen | Energia |
| PKO | PKO Bank Polski | Bankowość |
| PZU | PZU | Ubezpieczenia |
| KGH | KGHM | Surowce |
| LPP | LPP | Handel |
| CDR | CD Projekt | Gry/Technologia |
| ALE | Allegro | E-commerce |
| MBK | mBank | Bankowość |
| DNP | Dino Polska | Handel |
| CPS | Cyfrowy Polsat | Media/Telco |

---

## 📈 Przykładowe Wyniki (placeholder)

Po uruchomieniu pipeline w folderze `data/processed/` pojawi się `merged_dataset.csv` o strukturze:

```
date        | ticker | close | return_1d | sentiment_avg | sentiment_lag1 | sentiment_lag2
2024-01-15  | PKO    | 47.20 | +1.2%     | 0.34          | -0.12          | 0.08
2024-01-15  | CDR    | 168.50| -0.8%     | -0.67         | 0.21           | -0.45
```

---

## 🧪 Testy

```bash
pytest tests/ -v
pytest tests/test_scrapers.py      # Test czy scrapery działają
pytest tests/test_sentiment.py     # Test modelu NLP
```

---

## 📝 Roadmap

- [x] Struktura projektu i dokumentacja
- [ ] Implementacja scraperów (Bankier, Money.pl)
- [ ] Integracja FinBERT (model wielojęzyczny lub przetłumaczony)
- [ ] Moduł agregacji dziennej
- [ ] Testy Grangera i lag analysis
- [ ] Model ARIMAX
- [ ] Dashboard Plotly/Dash
- [ ] Raport PDF z wynikami

---

## ⚠️ Uwagi Implementacyjne

**FinBERT a język polski:** Oryginalny FinBERT jest wytrenowany na tekstach angielskich. Możliwe podejścia:
1. **Tłumaczenie nagłówków** — `deep-translator` (Google Translate API, darmowy tier) przed podaniem do FinBERT
2. **HerBERT** — polski model BERT od Allegro (`allegro/herbert-base-cased`), fine-tune na polskich tekstach finansowych
3. **Podejście hybrydowe** — HerBERT do klasyfikacji + VADER na przetłumaczonych tekstach jako baseline

Rekomendacja: użyj tłumaczenia + FinBERT jako głównego modelu, HerBERT jako porównania — to świetny materiał do sekcji "Porównanie modeli" w portfolio.

---

## 👤 Autor

Wojciech Sitek


---

*Projekt edukacyjny. Dane służą wyłącznie do celów badawczych.*
