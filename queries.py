"""
Ola Ride Insights - SQL layer
-----------------------------
All SQL used by the Streamlit app lives here, so it can be tested and
reused without importing Streamlit. The statements use standard SQL and run
unchanged on MySQL (production) and SQLite (CSV fallback for deployment).

Table: ola_rides  (one row per booking, see 01_create_table.sql)
"""

from __future__ import annotations

import re
from datetime import date

# --------------------------------------------------------------------------
# The 10 business questions from the project brief
# --------------------------------------------------------------------------
QUERIES: list[dict] = [
    {
        "id": 1,
        "title": "Retrieve all successful bookings",
        "sql": """SELECT *
FROM ola_rides
WHERE booking_status = 'Success'""",
        "insight": "63,967 of the 103,024 bookings (62.1%) were completed successfully.",
        "chart": None,
    },
    {
        "id": 2,
        "title": "Average ride distance for each vehicle type",
        "sql": """SELECT vehicle_type,
       ROUND(AVG(ride_distance), 2) AS avg_ride_distance_km
FROM ola_rides
WHERE booking_status = 'Success'
GROUP BY vehicle_type
ORDER BY avg_ride_distance_km DESC""",
        "insight": "Autos average only about 10 km per trip; every other vehicle type averages about 25 km. "
                   "(Successful rides only: cancelled rides have distance 0.)",
        "chart": {"x": "vehicle_type", "y": "avg_ride_distance_km"},
    },
    {
        "id": 3,
        "title": "Total number of cancelled rides by customers",
        "sql": """SELECT COUNT(*) AS cancelled_by_customers
FROM ola_rides
WHERE booking_status = 'Canceled by Customer'""",
        "insight": "10,499 rides (10.2% of all bookings) were cancelled by customers.",
        "chart": None,
    },
    {
        "id": 4,
        "title": "Top 5 customers who booked the highest number of rides",
        "sql": """SELECT customer_id,
       COUNT(*)           AS total_rides,
       SUM(booking_value) AS total_booking_value
FROM ola_rides
GROUP BY customer_id
ORDER BY total_rides DESC, total_booking_value DESC
LIMIT 5""",
        "insight": "Repeat booking is rare: only one customer booked 5 rides, and most customers booked once. "
                   "Ties are broken by total booking value.",
        "chart": {"x": "customer_id", "y": "total_rides"},
    },
    {
        "id": 5,
        "title": "Rides cancelled by drivers due to personal and car-related issues",
        "sql": """SELECT COUNT(*) AS driver_cancels_personal_car_issue
FROM ola_rides
WHERE driver_cancel_reason = 'Personal & Car related issue'""",
        "insight": "6,542 driver cancellations were for personal or car-related issues, "
                   "the largest driver cancellation reason.",
        "chart": None,
    },
    {
        "id": 6,
        "title": "Maximum and minimum driver ratings for Prime Sedan bookings",
        "sql": """SELECT MAX(driver_rating) AS max_driver_rating,
       MIN(driver_rating) AS min_driver_rating
FROM ola_rides
WHERE vehicle_type = 'Prime Sedan'""",
        "insight": "Prime Sedan driver ratings span the full 3.0 to 5.0 range.",
        "chart": None,
    },
    {
        "id": 7,
        "title": "Rides where payment was made using UPI",
        "sql": """SELECT *
FROM ola_rides
WHERE payment_method = 'UPI'""",
        "insight": "25,881 rides were paid by UPI, second only to cash (35,022).",
        "chart": None,
    },
    {
        "id": 8,
        "title": "Average customer rating per vehicle type",
        "sql": """SELECT vehicle_type,
       ROUND(AVG(customer_rating), 2) AS avg_customer_rating
FROM ola_rides
GROUP BY vehicle_type
ORDER BY avg_customer_rating DESC""",
        "insight": "Customer ratings are almost identical across vehicle types (about 4.0), "
                   "so ratings do not point to a weak vehicle type.",
        "chart": {"x": "vehicle_type", "y": "avg_customer_rating"},
    },
    {
        "id": 9,
        "title": "Total booking value of rides completed successfully",
        "sql": """SELECT SUM(booking_value) AS total_booking_value_successful
FROM ola_rides
WHERE booking_status = 'Success'""",
        "insight": "Completed rides generated a total booking value of 35,080,467. "
                   "Cancelled rides also carry a booking value, so they are excluded.",
        "chart": None,
    },
    {
        "id": 10,
        "title": "All incomplete rides along with the reason",
        "sql": """SELECT booking_id,
       booking_date,
       customer_id,
       vehicle_type,
       booking_status,
       incomplete_reason
FROM ola_rides
WHERE incomplete_ride = 'Yes'""",
        "insight": "3,926 rides ended incomplete. Top reasons: Customer Demand (1,601) "
                   "and Vehicle Breakdown (1,591), then Other Issue (734).",
        "chart": None,
    },
]


# --------------------------------------------------------------------------
# Overview page: filter-aware SQL
# --------------------------------------------------------------------------
def build_where(vehicles: list[str], start: date, end: date) -> str:
    """Build a WHERE clause from the sidebar filters.

    Dates arrive as `date` objects and vehicle names come from a list read
    from the database; quotes are escaped anyway.
    """
    conditions = [f"booking_date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'"]
    if vehicles:
        quoted = ", ".join("'" + v.replace("'", "''") + "'" for v in vehicles)
        conditions.append(f"vehicle_type IN ({quoted})")
    return "WHERE " + " AND ".join(conditions)


def kpi_sql(where: str) -> str:
    return f"""SELECT COUNT(*) AS total_rides,
       SUM(is_success) AS successful_rides,
       SUM(CASE WHEN cancel_type <> 'Not Cancelled' THEN 1 ELSE 0 END) AS cancelled_rides,
       SUM(CASE WHEN is_success = 1 THEN booking_value ELSE 0 END) AS revenue
FROM ola_rides
{where}"""


def status_sql(where: str) -> str:
    return f"""SELECT booking_status, COUNT(*) AS rides
FROM ola_rides
{where}
GROUP BY booking_status
ORDER BY rides DESC"""


def daily_sql(where: str) -> str:
    return f"""SELECT booking_date, COUNT(*) AS rides
FROM ola_rides
{where}
GROUP BY booking_date
ORDER BY booking_date"""


def vehicles_sql() -> str:
    return "SELECT DISTINCT vehicle_type FROM ola_rides ORDER BY vehicle_type"


def date_range_sql() -> str:
    return "SELECT MIN(booking_date) AS first_day, MAX(booking_date) AS last_day FROM ola_rides"


# --------------------------------------------------------------------------
# Custom SQL page: very small safety check (read-only SELECT statements)
# --------------------------------------------------------------------------
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|replace|grant|revoke|call|exec)\b",
    re.IGNORECASE,
)


def validate_select(sql: str) -> str | None:
    """Return an error message if `sql` is not a single read-only SELECT, else None."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        return "Please type a query."
    if not cleaned.lower().startswith("select"):
        return "Only SELECT queries are allowed."
    if ";" in cleaned:
        return "Please run one statement at a time."
    if _FORBIDDEN.search(cleaned):
        return "That query contains a keyword that is not allowed."
    return None