"""
Analiza sentymentu nagłówków newsów przy użyciu FinBERT.
Pipeline: Polski tekst → Tłumaczenie EN → FinBERT → wynik [-1, 1]
"""
import pandas as pd
import numpy as np
import yaml
import os
from loguru import logger


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def translate_to_english(texts: list[str]) -> list[str]:
    """Tłumaczy listę polskich tekstów na angielski (Google Translate, darmowy tier)."""
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source="pl", target="en")
    translated = []
    for text in texts:
        try:
            result = translator.translate(text)
            translated.append(result if result else text)
        except Exception as e:
            logger.warning(f"Błąd tłumaczenia: {e} — używam oryginału.")
            translated.append(text)
    return translated


def run_finbert(texts: list[str], batch_size: int = 16) -> list[dict]:
    """
    Uruchamia FinBERT na liście tekstów.

    Returns:
        Lista słowników: [{"label": "positive"|"negative"|"neutral", "score": float}]
    """
    from transformers import pipeline

    logger.info("Ładowanie modelu FinBERT (pierwsze uruchomienie pobierze ~400MB)...")
    nlp_pipeline = pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        tokenizer="ProsusAI/finbert",
        truncation=True,
        max_length=512
    )

    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"FinBERT — batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        batch_results = nlp_pipeline(batch)
        results.extend(batch_results)

    return results


def label_to_score(label: str, score: float) -> float:
    """
    Konwertuje label FinBERT na liczbę ciągłą:
    positive →  +score
    negative →  -score
    neutral  →   0
    """
    if label == "positive":
        return score
    elif label == "negative":
        return -score
    return 0.0


def run_sentiment(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    input_path = config["paths"]["raw_news"]
    output_path = config["paths"]["sentiment_daily"]
    translate = config["nlp"]["translation_enabled"]
    batch_size = config["nlp"]["batch_size"]

    if not os.path.exists(input_path):
        logger.error(f"Brak pliku z newsami: {input_path}. Uruchom najpierw moduł ingestion.")
        return

    df = pd.read_csv(input_path)
    logger.info(f"Załadowano {len(df)} artykułów z {input_path}")

    titles = df["title"].fillna("").tolist()

    # Krok 1: Tłumaczenie PL → EN
    if translate:
        logger.info("Tłumaczenie nagłówków PL → EN...")
        titles_en = translate_to_english(titles)
        df["title_en"] = titles_en
    else:
        df["title_en"] = titles

    # Krok 2: FinBERT
    logger.info("Uruchamianie FinBERT...")
    finbert_results = run_finbert(df["title_en"].tolist(), batch_size=batch_size)

    df["sentiment_label"] = [r["label"] for r in finbert_results]
    df["sentiment_confidence"] = [r["score"] for r in finbert_results]
    df["sentiment_score"] = [
        label_to_score(r["label"], r["score"]) for r in finbert_results
    ]

    # Krok 3: Agregacja do dziennego sentymentu per spółka
    df["date"] = pd.to_datetime(df["published_at"], errors="coerce").dt.date

    daily_sentiment = (
        df.groupby(["date", "ticker_mentioned"])
        .agg(
            sentiment_mean=("sentiment_score", "mean"),
            sentiment_std=("sentiment_score", "std"),
            article_count=("sentiment_score", "count"),
            positive_pct=("sentiment_label", lambda x: (x == "positive").mean()),
            negative_pct=("sentiment_label", lambda x: (x == "negative").mean()),
        )
        .reset_index()
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    daily_sentiment.to_csv(output_path, index=False)
    logger.success(f"Sentyment dzienny zapisany do: {output_path}")
    logger.info(f"Przykład:\n{daily_sentiment.head()}")


if __name__ == "__main__":
    run_sentiment()
