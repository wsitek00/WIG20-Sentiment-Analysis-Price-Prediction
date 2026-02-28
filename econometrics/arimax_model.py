"""
Model ARIMAX: cena ~ ARIMA(p,d,q) + sentyment jako zmienna egzogenna.

Dla każdej spółki z istotnymi wynikami Grangera:
1. Dobieramy rząd ARIMA (auto_arima lub grid search)
2. Dodajemy optymalny lag sentymentu jako egzogenną
3. Porównujemy ARIMA vs ARIMAX (AIC, RMSE)
4. Zapisujemy wyniki
"""
import pandas as pd
import numpy as np
import yaml
import os
import warnings
warnings.filterwarnings('ignore')

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import arma_order_select_ic
from sklearn.metrics import mean_squared_error
from loguru import logger


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def find_best_arima_order(series: pd.Series, max_p: int = 3, max_q: int = 3) -> tuple:
    """Prosta siatka p,q — szuka najniższego AIC."""
    best_aic = np.inf
    best_order = (1, 0, 0)

    for p in range(0, max_p + 1):
        for q in range(0, max_q + 1):
            if p == 0 and q == 0:
                continue
            try:
                model = ARIMA(series.dropna(), order=(p, 0, q))
                result = model.fit()
                if result.aic < best_aic:
                    best_aic = result.aic
                    best_order = (p, 0, q)
            except Exception:
                continue

    return best_order, best_aic


def fit_arimax(series: pd.Series, exog: pd.Series, order: tuple) -> dict:
    """Dopasowuje model ARIMAX i zwraca metryki."""
    # Train/test split 80/20
    n = len(series)
    split = int(n * 0.8)

    train_y = series.iloc[:split]
    test_y = series.iloc[split:]
    train_x = exog.iloc[:split].values.reshape(-1, 1)
    test_x = exog.iloc[split:].values.reshape(-1, 1)

    try:
        # ARIMA baseline (bez sentymentu)
        arima = ARIMA(train_y, order=order).fit()
        arima_pred = arima.forecast(steps=len(test_y))
        arima_rmse = np.sqrt(mean_squared_error(test_y, arima_pred))
        arima_aic = arima.aic

        # ARIMAX (z sentymentem)
        arimax = ARIMA(train_y, exog=train_x, order=order).fit()
        arimax_pred = arimax.forecast(steps=len(test_y), exog=test_x)
        arimax_rmse = np.sqrt(mean_squared_error(test_y, arimax_pred))
        arimax_aic = arimax.aic

        improvement = (arima_rmse - arimax_rmse) / arima_rmse * 100

        return {
            "arima_aic": round(arima_aic, 2),
            "arimax_aic": round(arimax_aic, 2),
            "arima_rmse": round(arima_rmse, 6),
            "arimax_rmse": round(arimax_rmse, 6),
            "rmse_improvement_pct": round(improvement, 2),
            "sentiment_coef": round(arimax.params.get("x1", np.nan), 6),
            "sentiment_pvalue": round(arimax.pvalues.get("x1", np.nan), 4),
            "order": str(order),
            "n_train": split,
            "n_test": len(test_y),
        }
    except Exception as e:
        logger.warning(f"Błąd ARIMAX: {e}")
        return {}


def run_arimax(config_path: str = "config.yaml") -> pd.DataFrame:
    config = load_config(config_path)
    merged_path = config["paths"]["merged"]
    granger_path = "data/processed/granger_results.csv"

    if not os.path.exists(merged_path):
        logger.error(f"Brak pliku: {merged_path}")
        return pd.DataFrame()

    merged = pd.read_csv(merged_path, parse_dates=["date"])
    granger = pd.read_csv(granger_path) if os.path.exists(granger_path) else pd.DataFrame()

    # Wybierz spółki z istotnymi wynikami Grangera
    if not granger.empty:
        sig_tickers = granger[granger["significant"]]["ticker"].unique()
    else:
        sig_tickers = merged["ticker"].unique()

    if len(sig_tickers) == 0:
        logger.warning("Brak spółek z istotnymi wynikami Grangera — testuję wszystkie.")
        sig_tickers = merged["ticker"].unique()

    logger.info(f"ARIMAX dla spółek: {list(sig_tickers)}")

    all_results = []

    for ticker in sig_tickers:
        df_t = merged[merged["ticker"] == ticker].sort_values("date").copy()

        # Znajdź optymalny lag sentymentu (najniższe p-value Grangera)
        best_lag = 1
        if not granger.empty:
            g_ticker = granger[(granger["ticker"] == ticker) & (granger["significant"])]
            if not g_ticker.empty:
                best_lag = int(g_ticker.loc[g_ticker["p_value"].idxmin(), "lag_days"])

        lag_col = f"sentiment_lag{best_lag}" if best_lag <= 6 else "sentiment_lag1"
        if lag_col not in df_t.columns:
            lag_col = "sentiment_lag1"

        df_t = df_t.dropna(subset=["log_return", lag_col])

        if len(df_t) < 30:
            logger.warning(f"{ticker}: Za mało obserwacji ({len(df_t)}) — pomijam.")
            continue

        series = df_t["log_return"].reset_index(drop=True)
        exog = df_t[lag_col].reset_index(drop=True)

        logger.info(f"\n{'='*50}")
        logger.info(f"ARIMAX dla: {ticker} | best_lag={best_lag} | n={len(df_t)}")

        # Dobierz rząd ARIMA
        order, base_aic = find_best_arima_order(series)
        logger.info(f"  Optymalny rząd ARIMA: {order} (AIC={base_aic:.1f})")

        # Dopasuj i porównaj modele
        results = fit_arimax(series, exog, order)

        if results:
            results["ticker"] = ticker
            results["best_sentiment_lag"] = best_lag

            logger.info(f"  ARIMA  RMSE: {results['arima_rmse']:.6f} | AIC: {results['arima_aic']:.1f}")
            logger.info(f"  ARIMAX RMSE: {results['arimax_rmse']:.6f} | AIC: {results['arimax_aic']:.1f}")
            logger.info(f"  Poprawa RMSE: {results['rmse_improvement_pct']:+.1f}%")
            logger.info(f"  Współczynnik sentymentu: {results['sentiment_coef']:.6f} (p={results['sentiment_pvalue']:.4f})")

            marker = "✓ Sentyment istotny!" if results['sentiment_pvalue'] < 0.05 else "✗ Sentyment nieistotny"
            logger.info(f"  → {marker}")

            all_results.append(results)

    if not all_results:
        logger.error("Brak wyników ARIMAX.")
        return pd.DataFrame()

    final_df = pd.DataFrame(all_results)
    cols = ["ticker", "order", "best_sentiment_lag", "arima_aic", "arimax_aic",
            "arima_rmse", "arimax_rmse", "rmse_improvement_pct",
            "sentiment_coef", "sentiment_pvalue", "n_train", "n_test"]
    final_df = final_df[[c for c in cols if c in final_df.columns]]

    output_path = "data/processed/arimax_results.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)

    logger.info(f"\n{'='*50}")
    logger.info("PODSUMOWANIE ARIMAX:")
    logger.info(f"\n{final_df.to_string(index=False)}")
    logger.success(f"Wyniki zapisane do: {output_path}")

    return final_df


if __name__ == "__main__":
    run_arimax()