
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = [
    {"name": "Lahore", "latitude": 31.5204, "longitude": 74.3587},
    {"name": "Karachi", "latitude": 24.8607, "longitude": 67.0011},
    {"name": "Islamabad", "latitude": 33.6844, "longitude": 73.0479},
]

OUTPUT_DIR = Path("data/sample/bronze")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def fetch_weather(city, run_id):
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "UTC",
        "forecast_days": 7,
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    maximum = daily.get("temperature_2m_max", [])
    minimum = daily.get("temperature_2m_min", [])

    if not dates or len(dates) != len(maximum) or len(dates) != len(minimum):
        raise ValueError(f"Invalid daily data returned for {city['name']}")

    result = {
        "city": city["name"],
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "daily": daily,
    }

    output_dir = OUTPUT_DIR / f"run_date={run_id[:10]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{city['name'].lower()}_{run_id}.json"
    output_file.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    logging.info("Saved %s: %s records", city["name"], len(dates))
    return len(dates)


def main():
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    successful = 0

    for city in CITIES:
        try:
            count = fetch_weather(city, run_id)
            successful += 1
            logging.info("%s completed with %s records", city["name"], count)
        except (requests.RequestException, ValueError, KeyError) as error:
            logging.error("%s failed: %s", city["name"], error)

    if successful != len(CITIES):
        raise RuntimeError(
            f"Only {successful} of {len(CITIES)} cities succeeded"
        )

    logging.info("Batch completed successfully: %s", run_id)


if __name__ == "__main__":
    main()
