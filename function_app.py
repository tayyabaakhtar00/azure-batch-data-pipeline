import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
import requests
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(
    http_auth_level=func.AuthLevel.FUNCTION
)

API_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = [
    {"name": "Lahore", "latitude": 31.5204, "longitude": 74.3587},
    {"name": "Karachi", "latitude": 24.8607, "longitude": 67.0011},
    {"name": "Islamabad", "latitude": 33.6844, "longitude": 73.0479},
]


@app.route(route="fetch-weather", methods=["GET", "POST"])
def fetch_weather_http(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Weather ingestion function started.")

    connection_string = os.environ.get(
        "WEATHER_STORAGE_CONNECTION_STRING"
    )

    if not connection_string:
        return func.HttpResponse(
            "Missing WEATHER_STORAGE_CONNECTION_STRING app setting.",
            status_code=500,
        )

    try:
        blob_service = BlobServiceClient.from_connection_string(
            connection_string
        )
        container = blob_service.get_container_client("bronze")

        run_id = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H-%M-%SZ"
        )
        uploaded = []

        for city in CITIES:
            params = {
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "UTC",
                "forecast_days": 7,
            }

            response = requests.get(
                API_URL,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            daily = data.get("daily", {})
            dates = daily.get("time", [])
            maximum = daily.get("temperature_2m_max", [])
            minimum = daily.get("temperature_2m_min", [])

            if (
                not dates
                or len(dates) != len(maximum)
                or len(dates) != len(minimum)
            ):
                raise ValueError(
                    f"Invalid daily data for {city['name']}"
                )

            result = {
                "city": city["name"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "daily": daily,
            }

            blob_name = (
                f"run_date={run_id[:10]}/"
                f"{city['name'].lower()}_{run_id}.json"
            )

            container.upload_blob(
                name=blob_name,
                data=json.dumps(result, indent=2),
                overwrite=True,
            )

            uploaded.append({
                "city": city["name"],
                "blob": blob_name,
                "records": len(dates),
            })

        logging.info("Uploaded weather data for all cities.")

        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "run_id": run_id,
                "uploaded": uploaded,
            }),
            mimetype="application/json",
            status_code=200,
        )

    except (requests.RequestException, ValueError, KeyError) as error:
        logging.exception("Weather ingestion failed.")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(error)}),
            mimetype="application/json",
            status_code=502,
        )
    except Exception:
        logging.exception("Unexpected weather ingestion error.")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Unexpected ingestion error. Check function logs.",
            }),
            mimetype="application/json",
            status_code=500,
        )
