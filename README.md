# Ola Ride Insights

An end-to-end analytics project on Ola ride-sharing data (July 2024): data cleaning in Python, analysis in SQL, an interactive Power BI dashboard, and a Streamlit web app.

- **Live app:** `ADD YOUR STREAMLIT LINK HERE`
- **Dataset:** 103,024 bookings, 1 to 31 July 2024

## Tech stack

Python (Pandas) · MySQL · SQL · Power BI · Streamlit · Git/GitHub

## Project structure

```
ola-ride-insights/
├── app.py                  Streamlit app (4 pages)
├── queries.py              All SQL used by the app
├── requirements.txt        Python dependencies
├── data/ola_cleaned.csv    Cleaned dataset used by the deployed app
├── data/raw/               Original dataset (OLA_DataSet.xlsx)
├── dashboard_images/       Screenshots of the 5 Power BI pages
├── sql/                    01_create_table.sql, 03_queries.sql
├── python/                 clean_ola_data.py, 02_load_to_mysql.py
└── powerbi/                Power BI report (.pbix)
```

## How the project was built

1. **Clean** (`python/clean_ola_data.py`): renamed columns to snake_case, split the raw date/time into a proper date, time and timestamp, added derived features (`booking_hour`, `day_name`, `is_weekend`, `time_slot`, `is_success`, `cancel_type`) and ran 9 validation checks.
2. **Load** (`sql/01_create_table.sql`, `python/02_load_to_mysql.py`): created the `ola_db.ola_rides` table with typed columns and indexes, and loaded the cleaned CSV into MySQL.
3. **Analyse** (`sql/03_queries.sql`): answered the 10 business questions, each validated against Pandas.
4. **Visualise**: built a 5-page Power BI dashboard on top of the MySQL data.
5. **Publish**: built the Streamlit app that presents the SQL results, filters and the dashboard.

## Data notes

- Missing values in `payment_method`, ratings, `v_tat`, `c_tat` and the reason columns are **structural**: a cancelled ride has no payment or rating. They are kept as NULL, not filled.
- Cancelled rides still carry a `booking_value` (with distance 0), so every revenue figure filters on successful rides.
- "Incomplete" rides are recorded inside the `Success` status and flagged by `incomplete_ride = 'Yes'`.

## SQL questions and answers

| # | Question | Result |
|---|---|---|
| 1 | All successful bookings | 63,967 rows |
| 2 | Average ride distance per vehicle type (successful rides) | Auto 10.04 km; all others about 25 km |
| 3 | Rides cancelled by customers | 10,499 |
| 4 | Top 5 customers by number of rides | CID954071 (5 rides), then four customers with 4 rides |
| 5 | Driver cancellations: personal and car-related issues | 6,542 |
| 6 | Prime Sedan driver ratings | Max 5.0, min 3.0 |
| 7 | Rides paid by UPI | 25,881 |
| 8 | Average customer rating per vehicle type | About 4.0 for every type |
| 9 | Total booking value of successful rides | 35,080,467 |
| 10 | Incomplete rides with reasons | 3,926 rows |

## Power BI dashboard

Five pages with a shared date range and vehicle type filter (synced across pages):

| Page | Contents |
|---|---|
| Overall | KPI cards (total rides, success rate, cancellation rate, revenue, average booking value), ride volume over time, booking status breakdown, rides by hour |
| Vehicle Type | Table with icons: total booking value, success booking value, average and total distance |
| Revenue | Revenue by payment method, top 5 customers by booking value, ride distance per day |
| Cancellation | Cancellation reasons for customers and for drivers |
| Ratings | Driver and customer ratings by vehicle type, driver rating distribution, daily customer vs. driver ratings |

Screenshots are in `dashboard_images/`.

## Key insights

1. **Only 62.1% of bookings are completed.** 17.9% are cancelled by drivers, 10.2% by customers, and 9.8% end with no driver found. Reducing cancellations is the biggest opportunity.
2. **Driver behaviour drives customer cancellations.** "Driver is not moving towards pickup location" (3,175) and "Driver asked to cancel" (2,670) make up 55.7% of customer cancellations.
3. **Driver cancellations are mostly personal or car-related.** That reason alone accounts for 6,542 of 18,434 driver cancellations.
4. **Cash and UPI bring in about 95% of revenue** (cash 19.3M, UPI 14.2M). Cards are marginal.
5. **Demand is steady.** Daily rides stay between 3,072 and 3,432 and hourly demand is flat at about 4.2K to 4.4K, so driver supply should be spread across the day instead of concentrated in peaks. 31 July is the lowest day.
6. **Autos run short trips** (about 10 km on average versus about 25 km for every other vehicle type).
7. **Ratings are uniform.** Drivers and customers both average about 4.0 for every vehicle type, so ratings do not point to a weak vehicle type.
8. **Repeat usage is low.** 94,544 unique customers made 103,024 bookings; most booked once.

## Assumptions

- **Revenue** counts successful rides only.
- **Cancellation rate** counts customer and driver cancellations; "Driver Not Found" is reported separately.
- **Average distance (Q2)** uses successful rides only, because cancelled rides have distance 0.
- **Top customers (Q4)** ties are broken by total booking value. The Power BI "Top 5 customers" chart ranks by booking value of successful rides instead.

## Run it locally

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

By default the app reads `data/ola_cleaned.csv`. To use your own MySQL database, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the connection details.

## Reproduce the cleaned data

The cleaned file is already included. To regenerate it from the original workbook:

```bash
pip install pandas openpyxl
python python/clean_ola_data.py data/raw/OLA_DataSet.xlsx data/ola_cleaned.csv
```

To load it into MySQL, run `sql/01_create_table.sql` in MySQL Workbench, then `python python/02_load_to_mysql.py` (run it from the folder that contains `ola_cleaned.csv`, or adjust `CSV_FILE` in the script).

## App pages

- **Overview:** KPIs and charts with vehicle type and date filters
- **SQL Insights:** the 10 questions, with the SQL shown, search, CSV download and an insight for each
- **Power BI Dashboard:** the five dashboard pages
- **Custom SQL:** run your own read-only `SELECT` query
