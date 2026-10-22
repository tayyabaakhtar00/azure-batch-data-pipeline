
import unittest
from pathlib import Path

import pandas as pd

GOLD_FILE = Path("data/sample/gold/daily_city_weather_summary.csv")


class TestGoldLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not GOLD_FILE.exists():
            raise FileNotFoundError(
                f"Gold file not found: {GOLD_FILE}. Run the Gold transformation first."
            )
        cls.df = pd.read_csv(GOLD_FILE)

    def test_required_columns_exist(self):
        required = {
            "date",
            "city",
            "average_max_temperature_c",
            "average_min_temperature_c",
            "forecast_days",
        }
        self.assertTrue(required.issubset(self.df.columns))

    def test_all_three_cities_exist(self):
        expected = {"Lahore", "Karachi", "Islamabad"}
        self.assertTrue(expected.issubset(set(self.df["city"])))

    def test_no_missing_values(self):
        self.assertFalse(self.df.isna().any().any())

    def test_no_duplicate_city_date_records(self):
        self.assertFalse(
            self.df.duplicated(subset=["date", "city"]).any()
        )

    def test_temperature_ranges_are_valid(self):
        self.assertTrue(
            (
                self.df["average_min_temperature_c"]
                <= self.df["average_max_temperature_c"]
            ).all()
        )

    def test_forecast_days_is_positive(self):
        self.assertTrue((self.df["forecast_days"] > 0).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
