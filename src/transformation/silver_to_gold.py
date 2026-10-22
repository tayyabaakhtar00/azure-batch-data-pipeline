
import logging
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
SILVER_DIR = BASE_DIR / "data" / "azure" / "silver"
GOLD_DIR = BASE_DIR / "data" / "azure" / "gold"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    files = sorted(SILVER_DIR.glob("run_id=*/weather.csv"))

    if not files:
        raise SystemExit(f"FAIL: No Azure Silver CSV files found in {SILVER_DIR}")

    frames = [pd.read_csv(file) for file in files]
    silver = pd.concat(frames, ignore_index=True)

    required = {
        "city", "date", "temperature_max_c",
        "temperature_min_c", "run_id"
    }
    missing = required - set(silver.columns)

    if missing:
        raise SystemExit(f"FAIL: Missing columns: {sorted(missing)}")

    silver["date"] = pd.to_datetime(silver["date"], errors="raise")
    silver["temperature_max_c"] = pd.to_numeric(
        silver["temperature_max_c"], errors="raise"
    )
    silver["temperature_min_c"] = pd.to_numeric(
        silver["temperature_min_c"], errors="raise"
    )

    if silver[list(required)].isna().any().any():
        raise SystemExit("FAIL: Required fields contain missing values.")

    if (silver["temperature_min_c"] > silver["temperature_max_c"]).any():
        raise SystemExit("FAIL: Minimum temperature exceeds maximum.")

    # Keep the latest ingestion run for each city and forecast date.
    silver = silver.sort_values("run_id")
    latest = silver.drop_duplicates(
        subset=["city", "date"],
        keep="last",
    )

    gold = (
        latest.groupby(["date", "city"], as_index=False)
        .agg(
            average_max_temperature_c=("temperature_max_c", "mean"),
            average_min_temperature_c=("temperature_min_c", "mean"),
            forecast_days=("date", "count"),
        )
    )

    gold["average_max_temperature_c"] = (
        gold["average_max_temperature_c"].round(2)
    )
    gold["average_min_temperature_c"] = (
        gold["average_min_temperature_c"].round(2)
    )

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    output_file = GOLD_DIR / "daily_city_weather_summary.csv"
    gold.to_csv(output_file, index=False, encoding="utf-8")

    logging.info("Azure Gold Layer saved: %s", output_file)
    logging.info("Gold records: %s", len(gold))
    logging.info("Cities: %s", sorted(gold["city"].unique()))


if __name__ == "__main__":
    main()
