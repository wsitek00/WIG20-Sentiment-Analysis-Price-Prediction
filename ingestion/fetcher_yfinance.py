"""
Pobieranie cen spółek WIG20 przez yfinance.
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
    """
    Pobiera historyczne ceny zamknięcia i wolumen dla wszystkich spółek z config.yaml.

    Returns:
        DataFrame z kolumnami: date, ticker, name, Open, High, Low, Close, Volume
    """
    import requests as req
    config = load_config(config_path)
    tickers_config = config["tickers"]
    price_col = config["econometrics"]["price_column"]

    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    symbols = [t["symbol"] for t in tickers_config]
    name_map = {t["symbol"]: t["name"] for t in tickers_config}

    logger.info(f"Pobieranie danych dla {len(symbols)} spółek naraz...")

    # Tworzymy sesję z nagłówkami przeglądarki — obejście blokady Yahoo
    session = req.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    try:
        raw = yf.download(
            tickers=symbols,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
            group_by="ticker",
            session=session
        )
    except Exception as e:
        logger.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

    if raw.empty:
        logger.error("yfinance zwróciło pusty DataFrame.")
        return pd.DataFrame()

    # Rozpakuj MultiIndex kolumn na osobne DataFrame'y per ticker
    all_data = []
    for symbol in symbols:
        try:
            if len(symbols) == 1:
                df = raw.copy()
            else:
                df = raw[symbol].copy()

            df = df.dropna(subset=["Close"])
            if df.empty:
                logger.warning(f"Brak danych dla {symbol} — pomijam.")
                continue

            df = df.reset_index()
            df.rename(columns={"Date": "date"}, inplace=True)
            df["ticker"] = symbol
            df["name"] = name_map.get(symbol, symbol)
            df["log_return"] = df["Close"].pct_change()

            cols = ["date", "ticker", "name", "Open", "High", "Low", "Close", "Volume", "log_return"]
            cols_available = [c for c in cols if c in df.columns]
            all_data.append(df[cols_available])
            logger.info(f"  ✓ {symbol}: {len(df)} sesji")

        except Exception as e:
            logger.warning(f"Problem z {symbol}: {e}")

    if not all_data:
        logger.error("Nie pobrano żadnych danych cenowych!")
        return pd.DataFrame()

    result = pd.concat(all_data, ignore_index=True)
    logger.success(f"Pobrano {len(result)} rekordów cenowych dla {len(all_data)} spółek.")
    return result


def save_prices(df: pd.DataFrame, output_path: str = "data/raw/prices_raw.csv") -> None:
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.success(f"Dane cenowe zapisane do: {output_path}")


if __name__ == "__main__":
    df = fetch_prices(days=90)
    print(df.head(10))
    save_prices(df)