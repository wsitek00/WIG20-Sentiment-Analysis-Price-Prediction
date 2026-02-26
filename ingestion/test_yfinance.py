"""
Skrypt diagnostyczny — uruchom go i wklej wynik.
Testuje różne sposoby pobierania danych GPW.
"""
import yfinance as yf
print(f"yfinance version: {yf.__version__}")

# Test 1: pojedynczy ticker bez parametrów
print("\n--- Test 1: PKO.WA basic ---")
try:
    t = yf.Ticker("PKO.WA")
    hist = t.history(period="5d")
    print(hist)
except Exception as e:
    print(f"BŁĄD: {e}")

# Test 2: inny format tickera
print("\n--- Test 2: PKO.WA period=1mo ---")
try:
    df = yf.download("PKO.WA", period="1mo", progress=False)
    print(df.tail(3))
except Exception as e:
    print(f"BŁĄD: {e}")

# Test 3: znany ticker US żeby sprawdzić czy yfinance w ogóle działa
print("\n--- Test 3: AAPL (test połączenia) ---")
try:
    df = yf.download("AAPL", period="5d", progress=False)
    print(df.tail(3))
except Exception as e:
    print(f"BŁĄD: {e}")