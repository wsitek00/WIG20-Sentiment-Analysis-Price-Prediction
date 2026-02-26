"""
Pobieranie cen spółek WIG20 przez yfinance.
Kompatybilne z yfinance >= 1.0.0
"""
import yfinance as yf
import pandas as pd
import yaml
from datetime import datetime, timedelta
from loguru import logger


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def fetch_prices(days: int = 90, config_path: str = "config.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    tickers_config = config["tickers"]

    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    symbols = [t["symbol"] for t in tickers_config]
    name_map = {t["symbol"]: t["name"] for t in tickers_config}

    logger.info(f"Pobieranie danych dla {len(symbols)} spolok naraz...")

    try:
        raw = yf.download(
            tickers=symbols,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
    except Exception as e:
        logger.error(f"Blad pobierania danych: {e}")
        return pd.DataFrame()

    if raw.empty:
        logger.error("yfinance zwrocilo pusty DataFrame.")
        return pd.DataFrame()

    all_data = []
    for symbol in symbols:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                df = raw.xs(symbol, axis=1, level=1).copy()
            else:
                df = raw.copy()

            df = df.dropna(subset=["Close"])
            if df.empty:
                logger.warning(f"Brak danych dla {symbol} — pomijam.")
                continue

            df = df.reset_index()
            df.rename(columns={"Date": "date"}, inplace=True)
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
            df["ticker"] = symbol
            df["name"] = name_map.get(symbol, symbol)
            df["log_return"] = df["Close"].pct_change()

            cols = ["date", "ticker", "name", "Open", "High", "Low", "Close", "Volume", "log_return"]
            cols_available = [c for c in cols if c in df.columns]
            all_data.append(df[cols_available])
            logger.info(f"  OK {symbol} ({name_map.get(symbol, '')}): {len(df)} sesji")

        except Exception as e:
            logger.warning(f"Problem z {symbol}: {e}")

    if not all_data:
        logger.error("Nie pobrano zadnych danych cenowych!")
        return pd.DataFrame()

    result = pd.concat(all_data, ignore_index=True)
    logger.success(f"Pobrano lacznie {len(result)} rekordow dla {len(all_data)} spolek.")
    return result


def save_prices(df: pd.DataFrame, output_path: str = "data/raw/prices_raw.csv") -> None:
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.success(f"Dane cenowe zapisane do: {output_path}")


if __name__ == "__main__":
    df = fetch_prices(days=90)
    if not df.empty:
        print(df.head(10))
        print(f"\nSpolki: {df['ticker'].unique()}")
        print(f"Zakres dat: {df['date'].min()} -> {df['date'].max()}")
    save_prices(df)