
import json
from pathlib import Path

ROOT = Path("data/sample/bronze")


def main():
    files = sorted(ROOT.glob("run_date=*/*.json"))

    if not files:
        raise SystemExit("FAIL: No batch JSON files found.")

    latest_run = {}
    for file in files:
        with file.open(encoding="utf-8") as f:
            data = json.load(f)

        required = {"city", "latitude", "longitude", "fetched_at", "run_id", "daily"}
        missing = required - data.keys()

        if missing:
            raise SystemExit(f"FAIL: {file} missing {sorted(missing)}")

        daily = data["daily"]
        dates = daily.get("time", [])
        maximum = daily.get("temperature_2m_max", [])
        minimum = daily.get("temperature_2m_min", [])

        if not dates or not (len(dates) == len(maximum) == len(minimum)):
            raise SystemExit(f"FAIL: Invalid daily arrays in {file}")

        latest_run[data["city"]] = data["run_id"]

    print(f"PASS: Validated {len(files)} JSON files.")
    print("Latest run IDs by city:")
    for city, run_id in sorted(latest_run.items()):
        print(f"  {city}: {run_id}")

    expected = {"Lahore", "Karachi", "Islamabad"}
    if not expected.issubset(latest_run):
        raise SystemExit(
            f"FAIL: Missing cities: {sorted(expected - latest_run.keys())}"
        )

    print("PASS: All three cities have valid data.")


if __name__ == "__main__":
    main()
