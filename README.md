# Azure Weather Data Engineering Pipeline

An end-to-end Azure Data Engineering project that automates weather data ingestion, transformation, storage, and analytics using Microsoft Azure.

## Project Overview

This project collects weather forecast data for three major Pakistani cities: **Lahore, Karachi, and Islamabad**.

It implements a Medallion Architecture (Bronze, Silver, Gold) to process weather data and generate analytical insights.

## Technologies Used

- **Python** – Weather data ingestion and processing
- **Azure Functions** – Automated API ingestion
- **Azure Data Lake Storage Gen2** – Data storage
- **Azure Data Factory** – Pipeline orchestration and scheduling
- **Azure Databricks** – Data transformation using PySpark
- **Delta Lake** – Analytics-ready data tables
- **Databricks SQL Dashboard** – Weather data visualization
- **GitHub** – Version control

## Pipeline Architecture

```text
Open-Meteo Weather API
         |
         v
    Azure Functions
         |
         v
  Azure Data Lake Gen2
     Bronze Layer
         |
         v
  Azure Databricks
     Silver Layer
         |
         v
  Azure Databricks
      Gold Layer
         |
         v
  Delta Lake Tables
         |
         v
 Databricks SQL Dashboard

Azure Data Factory orchestrates
the ingestion and Databricks job.
```

## Data Processing Layers

### Bronze Layer
Stores raw JSON weather forecast data collected from the Open-Meteo API.

### Silver Layer
Cleans, validates, and structures the raw weather data.

### Gold Layer
Produces analytics-ready datasets, including:

- `fact_weather_daily`
- `dim_city`
- `dim_date`

## Pipeline Automation

Azure Data Factory runs the ingestion and transformation workflow through the `PL_Weather_Daily` pipeline.

The `TR_Daily_Weather` trigger schedules the pipeline daily.

## Data Quality

The project includes validation checks for:

- Missing temperature values
- Duplicate city and date combinations
- Data consistency

## Analytics Dashboard

The Pakistan Weather Analytics Dashboard provides:

- Weather KPIs
- Temperature trends
- City comparisons

## Project Structure

```text
azure-batch-data-pipeline/
├── function_app.py
├── azure_bronze_to_silver_function.py
├── host.json
├── requirements.txt
├── notebooks/
│   ├── 01_bronze_to_silver.py
│   └── 02_silver_to_gold.py
├── src/
│   ├── ingestion/
│   └── transformation/
└── tests/
```

## Security

Sensitive credentials, local Azure settings, virtual environments, and downloaded datasets are excluded from version control.

## Future Improvements

- Add automated CI/CD deployment
- Expand weather data coverage
- Add pipeline monitoring and alerts
- Implement additional data quality tests

## Author

**Tayyaba Akhtar**

Azure Data Engineering | Python | Cloud Computing