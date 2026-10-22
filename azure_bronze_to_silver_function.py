import csv
import io
import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
from azure.storage.blob import BlobServiceClient

# Use your existing app = func.FunctionApp(...) declaration.
# Do not create a second FunctionApp instance.


@app.route(route="bronze-to-silver", methods=["GET", "POST"])
def bronze_to_silver(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Starting Bronze-to-Silver transformation.")

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

        bronze_container = blob_service.get_container_client("bronze")
        silver_container = blob_service.get_container_client("silver")

        rows = []
        required_fields = [
            "city",
            "date",
            "temperature_max",
            "temperature_min",
        ]

        # Read JSON files from Bronze.
        for blob in bronze_container.list_blobs():
            if not blob.name.lower().endswith(".json"):
                continue

            content = bronze_container.get_blob_client(
                blob.name
            ).download_blob().readall()

            data = json.loads(content)

            # Support either a single weather record or a list of records.
            records = data if isinstance(data, list) else [data]

            for record in records:
                if not isinstance(record, dict):
                    continue

                # Handle Open-Meteo's daily forecast JSON format.
                if (
                    isinstance(record.get("daily"), dict)
                    and isinstance(record.get("city"), str)
                ):
                    daily = record["daily"]
                    dates = daily.get("time", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])

                    for i, date in enumerate(dates):
                        if i >= len(max_temps) or i >= len(min_temps):
                            continue

                        rows.append({
                            "city": record["city"],
                            "date": date,
                            "temperature_max": max_temps[i],
                            "temperature_min": min_temps[i],
                        })

                # Also support JSON files containing already flattened rows.
                elif all(field in record for field in required_fields):
                    rows.append({
                        field: record[field]
                        for field in required_fields
                    })

        if not rows:
            return func.HttpResponse(
                "No compatible weather records found in Bronze. "
                "Check the JSON structure and city field names.",
                status_code=400,
            )

        # Validate values and remove duplicate city/date records.
        clean_rows = {}

        for row in rows:
            try:
                date = datetime.strptime(
                    str(row["date"]), "%Y-%m-%d"
                ).date().isoformat()

                max_temp = float(row["temperature_max"])
                min_temp = float(row["temperature_min"])

                if min_temp > max_temp:
                    continue

                city = str(row["city"]).strip()
                if not city:
                    continue

                clean_rows[(city, date)] = {
                    "city": city,
                    "date": date,
                    "temperature_max": max_temp,
                    "temperature_min": min_temp,
                }
            except (TypeError, ValueError):
                continue

        output = io.StringIO()
        columns = [
            "city",
            "date",
            "temperature_max",
            "temperature_min",
        ]

        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()

        for key in sorted(clean_rows):
            writer.writerow(clean_rows[key])

        run_id = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H-%M-%SZ"
        )
        output_blob = f"run_id={run_id}/weather.csv"

        silver_container.upload_blob(
            name=output_blob,
            data=output.getvalue().encode("utf-8"),
            overwrite=True,
            content_type="text/csv",
        )

        result = {
            "status": "success",
            "bronze_records_read": len(rows),
            "silver_records_written": len(clean_rows),
            "silver_blob": output_blob,
        }

        logging.info("Bronze-to-Silver completed: %s", result)

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json",
        )

    except Exception:
        logging.exception("Bronze-to-Silver transformation failed.")
        return func.HttpResponse(
            "Bronze-to-Silver transformation failed. "
            "Check the Azure Function logs.",
            status_code=500,
        )