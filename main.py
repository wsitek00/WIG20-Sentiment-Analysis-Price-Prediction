"""
WIG20 Sentiment Analysis — punkt wejścia
Użycie: python main.py --mode [full|ingest|sentiment|econometrics|dashboard]
"""
import argparse
from loguru import logger


def parse_args():
    parser = argparse.ArgumentParser(description="WIG20 Sentiment Analysis Pipeline")
    parser.add_argument(
        "--mode",
        choices=["full", "ingest", "sentiment", "econometrics", "dashboard"],
        default="full",
        help="Który moduł uruchomić"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Ile dni wstecz pobierać dane (domyślnie 90)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info(f"Uruchamianie pipeline w trybie: {args.mode}")

    if args.mode in ("full", "ingest"):
        logger.info("▶ Moduł 1: Ingestion — pobieranie danych...")
        from ingestion.pipeline_ingestion import run_ingestion
        run_ingestion(days=args.days)

    if args.mode in ("full", "sentiment"):
        logger.info("▶ Moduł 2: NLP — analiza sentymentu...")
        from processing.sentiment_finbert import run_sentiment
        run_sentiment()

    if args.mode in ("full", "econometrics"):
        logger.info("▶ Moduł 3: Ekonometria — testy i modele...")
        from econometrics.granger_causality import run_granger
        run_granger()

    if args.mode == "dashboard":
        logger.info("▶ Moduł 4: Dashboard...")
        from visualization.dashboard import run_dashboard
        run_dashboard()

    logger.success("Pipeline zakończony.")


if __name__ == "__main__":
    main()
