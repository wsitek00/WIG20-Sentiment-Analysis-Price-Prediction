"""
Agregator — łączy dane cenowe z sentymentem w jeden dataset.
Tworzy zmienne opóźnione (lagi) gotowe do analizy ekonometrycznej.
"""
import pandas as pd
import numpy as np
import yaml
import os
from loguru import logger


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def create_merged_dataset(config_path: str = "config.yaml") -> pd.DataFrame:
    """
    Łączy ceny i sentyment, tworzy lagi sentymentu (1–5 dni).

    Returns:
        DataFrame gotowy do analizy ekonometrycznej.
    """
    config = load_config(config_path)
    prices_path = config["paths"]["raw_prices"]
    sentiment_path = config["paths"]["sentiment_daily"]
    output_path = config["paths"]["merged"]
    max_lag = config["econometrics"]["max_lag_days"]

    # Wczytaj dane
    prices = pd.read_csv(prices_path, parse_dates=["date"])
    sentiment = pd.read_csv(sentiment_path, parse_dates=["date"])
    sentiment.rename(columns={"ticker_mentioned": "ticker"}, inplace=True)

    logger.info(f"Ceny: {len(prices)} wierszy | Sentyment: {len(sentiment)} wierszy")

    # Merge po dacie i tickerze
    merged = pd.merge(
        prices,
        sentiment,
        on=["date", "ticker"],
        how="left"
    )

    # Uzupełnij brakujący sentyment zerem (dni bez newsów = neutralny)
    sentiment_cols = ["sentiment_mean", "sentiment_std", "article_count", "positive_pct", "negative_pct"]
    for col in sentiment_cols:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # Dodaj lagi sentymentu
    merged = merged.sort_values(["ticker", "date"])
    for lag in range(1, min(max_lag, 6) + 1):
        merged[f"sentiment_lag{lag}"] = merged.groupby("ticker")["sentiment_mean"].shift(lag)

    # Logarytmiczne stopy zwrotu (jeśli nie ma)
    if "log_return" not in merged.columns:
        merged["log_return"] = merged.groupby("ticker")["Close"].transform(
            lambda x: np.log(x / x.shift(1))
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.success(f"Merged dataset zapisany do: {output_path} ({len(merged)} wierszy)")

    return merged


if __name__ == "__main__":
    df = create_merged_dataset()
    print(df.describe())
    print(df.head())