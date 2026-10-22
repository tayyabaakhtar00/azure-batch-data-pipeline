
import json
import logging
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
BRONZE_DIR = BASE_DIR / "data" / "azure" / "bronze"
SILVER_DIR = BASE_DIR / "data" / "azure" / "silver"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def transform_file(file_path: Path) -> pd.DataFrame:
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    daily = data["daily"]
    dates = daily["time"]
    maximum = daily["temperature_2m_max"]
    minimum = daily["temperature_2m_min"]

    if not dates or not (len(dates) == len(maximum) == len(minimum)):
        raise ValueError(f"Invalid daily arrays: {file_path}")

    df = pd.DataFrame({
        "city": data["city"],
        "date": dates,
        "temperature_max_c": maximum,
        "temperature_min_c": minimum,
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "fetched_at": data["fetched_at"],
        "run_id": data["run_id"],
    })

    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.strftime("%Y-%m-%d")
    df["temperature_max_c"] = pd.to_numeric(
        df["temperature_max_c"], errors="raise"
    )
    df["temperature_min_c"] = pd.to_numeric(
        df["temperature_min_c"], errors="raise"
    )

    if df[["temperature_max_c", "temperature_min_c"]].isna().any().any():
        raise ValueError(f"Missing temperature values: {file_path}")

    if (df["temperature_min_c"] > df["temperature_max_c"]).any():
        raise ValueError(f"Minimum temperature exceeds maximum: {file_path}")

    if df["city"].isna().any() or df["city"].eq("").any():
        raise ValueError(f"Missing city name: {file_path}")

    return df


def main():
    files = sorted(BRONZE_DIR.glob("run_date=*/*.json"))

    if not files:
        raise SystemExit(f"No Bronze JSON files found in {BRONZE_DIR}")

    frames = []

    for file_path in files:
        frames.append(transform_file(file_path))
        logging.info("Validated %s", file_path.name)

    silver = pd.concat(frames, ignore_index=True)
    silver = silver.drop_duplicates(
        subset=["city", "date", "run_id"], keep="last"
    )

    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    for run_id, run_df in silver.groupby("run_id", sort=True):
        safe_run_id = run_id.replace(":", "-")
        output_dir = SILVER_DIR / f"run_id={safe_run_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "weather.csv"
        run_df.to_csv(output_file, index=False, encoding="utf-8")
        logging.info("Saved %s (%s records)", output_file, len(run_df))

    logging.info(
        "Silver transformation complete: %s records from %s Bronze files",
        len(silver),
        len(files),
    )


if __name__ == "__main__":
    main()
