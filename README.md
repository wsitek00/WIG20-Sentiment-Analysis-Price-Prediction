# 📈 WIG20 Sentiment Analysis & Price Prediction

> Analiza wpływu sentymentu mediów finansowych na notowania spółek WIG20  
> *Informatyka i Ekonometria | Python · NLP · Ekonometria*

---

## 🎯 Cel Projektu

System automatycznie pobiera nagłówki newsów z polskich portali finansowych (Bankier.pl, Google News), przetwarza je modelem NLP **FinBERT**, a następnie bada statystyczną zależność między sentymentem medialnym a zmianami cen akcji spółek z indeksu WIG20.

**Hipoteza badawcza:** *Czy sentyment polskich mediów finansowych poprzedza (w sensie Grangera) zmiany cen spółek WIG20?*

**Odpowiedź:** ✅ Tak — dla LPP.WA i CDR.WA sentyment statystycznie poprzedza ruchy cen, a model ARIMAX z sentymentem osiąga **8.5% niższe RMSE** niż baseline.

---

## 📊 Wyniki

### Test Przyczynowości Grangera
Sentyment mediów **poprzedza** zmiany cen dla 2 z 8 analizowanych spółek:

| Spółka | Najlepszy lag | p-value | Interpretacja |
|--------|--------------|---------|---------------|
| **LPP.WA** | 1–9 dni | < 0.0001 | Silna zależność — sentyment dnia poprzedniego |
| **CDR.WA** | 5–10 dni | 0.0001 | Sentyment poprzedza cenę o ~1–2 tygodnie |

![Wyniki testu Grangera](data/processed/plot_granger_results.png)

---

### Heatmapa Korelacji: Sentyment(lag) vs Stopa Zwrotu
Korelacja Pearsona między sentymentem z opóźnieniem a dzienną stopą zwrotu. LPP.WA wyróżnia się korelacją −0.77 przy lag=1.

![Heatmapa korelacji](data/processed/plot_correlation_heatmap.png)

---

### Model ARIMAX — LPP.WA
Dodanie sentymentu mediów jako zmiennej egzogennej do modelu ARIMA(0,0,1) poprawia dokładność prognozy o **8.5%** (p=0.0025).

![ARIMAX vs ARIMA RMSE](data/processed/plot_LPP_rmse_comparison.png)

![ARIMAX prognoza](data/processed/plot_LPP_arimax_vs_arima.png)

---

## 🏗️ Architektura Systemu

```
wig20-sentiment/
│
├── 📁 ingestion/               # Moduł 1: Pobieranie danych
│   ├── scraper_bankier.py      # RSS Bankier.pl
│   ├── scraper_googlenews.py   # Google News RSS per spółka
│   ├── fetcher_yfinance.py     # Ceny WIG20 (yfinance)
│   └── pipeline_ingestion.py  # Orkiestrator
│
├── 📁 processing/              # Moduł 2: NLP
│   ├── sentiment_finbert.py    # FinBERT + tłumaczenie PL→EN
│   └── aggregator.py          # Agregacja → dzienny sentyment
│
├── 📁 econometrics/            # Moduł 3: Analiza ekonometryczna
│   ├── granger_causality.py   # Test przyczynowości Grangera
│   └── arimax_model.py        # Model ARIMAX z sentymentem
│
├── 📁 notebooks/               # Wyniki i wizualizacje
│   ├── 01_EDA.ipynb            # Eksploracyjna analiza danych
│   └── 03_ARIMAX_Results.ipynb # Wyniki modelu ARIMAX
│
├── config.yaml                 # Konfiguracja spółek i parametrów
├── requirements.txt
└── main.py                     # Punkt wejścia pipeline
```

---

## 🔧 Stack Technologiczny

| Warstwa | Technologia | Zastosowanie |
|---------|-------------|--------------|
| **Ingestion** | `yfinance`, `BeautifulSoup`, `requests` | Ceny GPW, scraping newsów |
| **NLP** | `transformers` (FinBERT), `deep-translator` | Sentyment PL→EN→FinBERT |
| **Przetwarzanie** | `pandas`, `numpy` | Czyszczenie, agregacja, lagi |
| **Ekonometria** | `statsmodels`, `scikit-learn` | Granger, ARIMA, ARIMAX |
| **Wizualizacja** | `matplotlib`, `seaborn` | Wykresy, heatmapy |
| **Utils** | `loguru`, `pyyaml`, `python-dotenv` | Logi, konfiguracja |

---

## 📐 Metodologia

### 1. Pobieranie Danych
- **Ceny:** yfinance → 10 spółek WIG20, dane dzienne OHLCV
- **Newsy:** Bankier.pl RSS + Google News RSS (per spółka, słowa kluczowe)
- **NLP:** nagłówek PL → Google Translate → FinBERT → score [-1, +1]
- **Agregacja:** średni dzienny sentyment per spółka + lagi 1–6 dni

### 2. Test Grangera
Sprawdzamy czy sentyment *poprzedza* zmiany cen (a nie tylko z nimi koreluje):
```
H₀: sentyment NIE pomaga prognozować cen
H₁: sentyment POMAGA prognozować ceny
```
Test F-statystyki dla opóźnień 1–10 dni sesyjnych. Warunek wstępny: stacjonarność szeregów (test ADF).

### 3. Model ARIMAX
```
log_return_t = ARIMA(p,d,q) + β · sentyment_{t-k} + ε_t
```
Porównanie ARIMA vs ARIMAX na zbiorze testowym (ostatnie 20% danych). Metryka jakości: RMSE.

---

## 🚀 Uruchomienie

```bash
git clone https://github.com/wsitek00/WIG20-Sentiment-Analysis-Price-Prediction.git
cd WIG20-Sentiment-Analysis-Price-Prediction
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Pełny pipeline
```bash
python -m ingestion.pipeline_ingestion    # Pobierz ceny i newsy
python -m processing.sentiment_finbert   # Analiza sentymentu FinBERT
python -m processing.aggregator          # Połącz dane
python -m econometrics.granger_causality # Testy Grangera
python -m econometrics.arimax_model      # Model ARIMAX
```

### Konfiguracja
Edytuj `config.yaml` aby zmienić spółki, zakres dat lub parametry:
```yaml
ingestion:
  days_back: 365   # Zmień dla dłuższej historii
nlp:
  translation_enabled: true
econometrics:
  max_lag_days: 10
```

---

## 🏢 Monitorowane Spółki

| Ticker | Spółka | Sektor |
|--------|--------|--------|
| PKN.WA | PKN Orlen | Energia |
| PKO.WA | PKO Bank Polski | Bankowość |
| PZU.WA | PZU | Ubezpieczenia |
| KGH.WA | KGHM | Surowce |
| LPP.WA | LPP | Handel |
| CDR.WA | CD Projekt | Gry / Technologia |
| ALE.WA | Allegro | E-commerce |
| MBK.WA | mBank | Bankowość |
| DNP.WA | Dino Polska | Handel |
| CPS.WA | Cyfrowy Polsat | Media / Telco |

---

## ⚠️ Ograniczenia i Kierunki Rozwoju

**Obecne ograniczenia:**
- Mała próba (90 dni = ~57 sesji) — wyniki wymagają walidacji na dłuższym szeregu
- FinBERT wytrenowany na tekstach angielskich — tłumaczenie PL→EN wprowadza szum
- Pojedynczy split train/test zamiast rolling window cross-validation

**Planowane rozszerzenia:**
- [ ] Rozszerzenie do 2 lat historii (`days_back: 730`)
- [ ] Porównanie FinBERT vs HerBERT (polski BERT od Allegro)
- [ ] Rolling window cross-validation
- [ ] Interaktywny dashboard (Plotly/Dash)

---

## 👤 Autor

**Wojciech Sitek**

---

*Projekt edukacyjny. Dane służą wyłącznie do celów badawczych.*