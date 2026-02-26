"""
Test przyczynowości Grangera: czy sentyment poprzedza zmiany cen WIG20?

H0: sentyment NIE pomaga prognozować cen (brak przyczynowości Grangera)
H1: sentyment POMAGA prognozować ceny
"""
import pandas as pd
import numpy as np
import yaml
import os
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from loguru import logger


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def check_stationarity(series: pd.Series, name: str) -> bool:
    """Test ADF na stacjonarność szeregu — warunek dla testu Grangera."""
    result = adfuller(series.dropna())
    p_value = result[1]
    is_stationary = p_value < 0.05
    status = "✓ stacjonarny" if is_stationary else "✗ niestacjonarny (rozważ różnicowanie)"
    logger.info(f"ADF [{name}]: p={p_value:.4f} — {status}")
    return is_stationary


def run_granger_for_ticker(
    merged_df: pd.DataFrame,
    ticker: str,
    max_lag: int = 10,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Przeprowadza test Grangera dla jednej spółki.

    Returns:
        DataFrame z wynikami dla każdego opóźnienia.
    """
    df_ticker = merged_df[merged_df["ticker"] == ticker].copy()
    df_ticker = df_ticker.sort_values("date").dropna(subset=["log_return", "sentiment_mean"])

    if len(df_ticker) < max_lag * 3:
        logger.warning(f"{ticker}: Za mało obserwacji ({len(df_ticker)}) — pomijam.")
        return pd.DataFrame()

    logger.info(f"\n{'='*50}")
    logger.info(f"Test Grangera dla: {ticker} (n={len(df_ticker)})")

    # Sprawdź stacjonarność
    check_stationarity(df_ticker["log_return"], f"{ticker} log_return")
    check_stationarity(df_ticker["sentiment_mean"], f"{ticker} sentiment")

    # Dane do testu: [zmienna zależna (Y), zmienna wyjaśniająca (X)]
    data = df_ticker[["log_return", "sentiment_mean"]].dropna().values

    results = []
    try:
        test_results = grangercausalitytests(data, maxlag=max_lag, verbose=False)

        for lag, result in test_results.items():
            # Używamy testu F (ssr_ftest)
            f_stat = result[0]["ssr_ftest"][0]
            p_value = result[0]["ssr_ftest"][1]
            significant = p_value < alpha

            results.append({
                "ticker": ticker,
                "lag_days": lag,
                "f_statistic": round(f_stat, 4),
                "p_value": round(p_value, 4),
                "significant": significant,
                "interpretation": "Sentyment → Cena ✓" if significant else "Brak zależności"
            })

            marker = "✓ ***" if p_value < 0.01 else ("✓ *" if significant else "")
            logger.info(f"  Lag={lag:2d}: F={f_stat:.3f}, p={p_value:.4f} {marker}")

    except Exception as e:
        logger.error(f"Błąd testu Grangera dla {ticker}: {e}")

    return pd.DataFrame(results)


def run_granger(config_path: str = "config.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    merged_path = config["paths"]["merged"]
    max_lag = config["econometrics"]["max_lag_days"]
    alpha = config["econometrics"]["significance_level"]

    if not os.path.exists(merged_path):
        logger.error(f"Brak pliku: {merged_path}. Uruchom najpierw moduły ingestion i sentiment.")
        return pd.DataFrame()

    merged_df = pd.read_csv(merged_path, parse_dates=["date"])
    tickers = merged_df["ticker"].unique()
    logger.info(f"Testy Grangera dla {len(tickers)} spółek, max_lag={max_lag}")

    all_results = []
    for ticker in tickers:
        result = run_granger_for_ticker(merged_df, ticker, max_lag=max_lag, alpha=alpha)
        if not result.empty:
            all_results.append(result)

    if not all_results:
        logger.error("Brak wyników testów.")
        return pd.DataFrame()

    final_df = pd.concat(all_results, ignore_index=True)

    # Podsumowanie
    significant = final_df[final_df["significant"]]
    logger.info(f"\n{'='*50}")
    logger.info(f"PODSUMOWANIE: {len(significant)} istotnych wyników (p < {alpha})")
    if not significant.empty:
        logger.info(f"\n{significant[['ticker','lag_days','p_value','interpretation']].to_string()}")

    output_path = "data/processed/granger_results.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.success(f"Wyniki zapisane do: {output_path}")

    return final_df


if __name__ == "__main__":
    run_granger()
