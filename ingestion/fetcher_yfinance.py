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
    config = load_config(config_path)
    tickers = config["tickers"]
    price_col = config["econometrics"]["price_column"]

    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    all_data = []

    for ticker_info in tickers:
        symbol = ticker_info["symbol"]
        name = ticker_info["name"]
        logger.info(f"Pobieranie danych dla: {symbol} ({name})")

        try:
            df = yf.download(
                symbol,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
                auto_adjust=True
            )

            if df.empty:
                logger.warning(f"Brak danych dla {symbol} — pomijam.")
                continue

            df = df.reset_index()
            df["ticker"] = symbol
            df["name"] = name

            # Oblicz logarytmiczne stopy zwrotu
            df["log_return"] = df[price_col].pct_change().apply(
                lambda x: x  # można zamienić na np.log(1+x) dla log returns
            )

            all_data.append(df[["Date", "ticker", "name", "Open", "High", "Low", "Close", "Volume", "log_return"]])

        except Exception as e:
            logger.error(f"Błąd pobierania {symbol}: {e}")

    if not all_data:
        logger.error("Nie pobrano żadnych danych cenowych!")
        return pd.DataFrame()

    result = pd.concat(all_data, ignore_index=True)
    result.rename(columns={"Date": "date"}, inplace=True)

    logger.success(f"Pobrano {len(result)} rekordów cenowych dla {len(tickers)} spółek.")
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
