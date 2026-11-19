"""
Ola Ride Insights - Step 2: Data Cleaning & Preprocessing
----------------------------------------------------------
Input : OLA_DataSet.xlsx  (sheet "July")
Output: ola_cleaned.csv   (ready to load into MySQL / Power BI)

Usage:
    python clean_ola_data.py
    python clean_ola_data.py path/to/OLA_DataSet.xlsx path/to/ola_cleaned.csv
"""

import sys
import pandas as pd

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "OLA_DataSet.xlsx"
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "ola_cleaned.csv"
SHEET = "July"

# --------------------------------------------------------------------------
# 1. LOAD
# --------------------------------------------------------------------------
df = pd.read_excel(INPUT_FILE, sheet_name=SHEET)
print(f"Loaded {df.shape[0]:,} rows x {df.shape[1]} columns from sheet '{SHEET}'")

# --------------------------------------------------------------------------
# 2. RENAME COLUMNS  (consistent snake_case, no spaces)
# --------------------------------------------------------------------------
df = df.rename(columns={
    "Date": "booking_date",
    "Time": "booking_time",
    "Booking_ID": "booking_id",
    "Booking_Status": "booking_status",
    "Customer_ID": "customer_id",
    "Vehicle_Type": "vehicle_type",
    "Pickup_Location": "pickup_location",
    "Drop_Location": "drop_location",
    "V_TAT": "v_tat",
    "C_TAT": "c_tat",
    "Canceled_Rides_by_Customer": "customer_cancel_reason",
    "Canceled_Rides_by_Driver": "driver_cancel_reason",
    "Incomplete_Rides": "incomplete_ride",
    "Incomplete_Rides_Reason": "incomplete_reason",
    "Booking_Value": "booking_value",
    "Payment_Method": "payment_method",
    "Ride_Distance": "ride_distance",
    "Driver_Ratings": "driver_rating",
    "Customer_Rating": "customer_rating",
    "Vehicle Images": "vehicle_image_url",
})

# --------------------------------------------------------------------------
# 3. STANDARDISE TEXT  (trim spaces; blank strings -> real NULL)
# --------------------------------------------------------------------------
text_cols = df.select_dtypes(include=["object", "string"]).columns.drop("booking_time")
for col in text_cols:
    df[col] = df[col].astype("string").str.strip().replace("", pd.NA)

# --------------------------------------------------------------------------
# 4. FIX DATA TYPES  (date + time)
# --------------------------------------------------------------------------
# The raw "Date" column also carries a time part, and "Time" repeats it.
# Combine date + time into one reliable timestamp, then split cleanly.
date_part = pd.to_datetime(df["booking_date"]).dt.strftime("%Y-%m-%d")
df["booking_datetime"] = pd.to_datetime(date_part + " " + df["booking_time"].astype(str))

df["booking_date"] = df["booking_datetime"].dt.date
df["booking_time"] = df["booking_datetime"].dt.time

# --------------------------------------------------------------------------
# 5. DERIVED FEATURES
# --------------------------------------------------------------------------
dt = df["booking_datetime"].dt
df["booking_hour"] = dt.hour
df["day_name"] = dt.day_name()
df["day_of_week"] = dt.dayofweek + 1            # 1 = Monday ... 7 = Sunday
df["is_weekend"] = (dt.dayofweek >= 5).map({True: "Weekend", False: "Weekday"})

# Time-of-day bucket, useful for the "peak demand hours" use case
bins = [-1, 5, 11, 16, 20, 23]
labels = ["Late Night (00-05)", "Morning (06-11)", "Afternoon (12-16)",
          "Evening (17-20)", "Night (21-23)"]
df["time_slot"] = pd.cut(df["booking_hour"], bins=bins, labels=labels).astype("string")

# Simple flags that make SQL / Power BI filters easier
df["is_success"] = (df["booking_status"] == "Success").astype(int)
df["cancel_type"] = "Not Cancelled"
df.loc[df["booking_status"] == "Canceled by Customer", "cancel_type"] = "Customer"
df.loc[df["booking_status"] == "Canceled by Driver", "cancel_type"] = "Driver"

# --------------------------------------------------------------------------
# 6. NULL HANDLING
# --------------------------------------------------------------------------
# Nulls in payment_method, ratings, v_tat, c_tat, incomplete_ride and the
# reason columns are STRUCTURAL (a cancelled ride has no payment or rating).
# We deliberately keep them as NULL instead of filling with averages.

# --------------------------------------------------------------------------
# 7. VALIDATION CHECKS  (each line should print OK)
# --------------------------------------------------------------------------
def check(name, condition):
    print(f"  [{'OK' if condition else 'FAIL'}] {name}")
    return bool(condition)

print("\nValidation:")
results = [
    check("103,024 rows kept", len(df) == 103_024),
    check("booking_id is unique", df["booking_id"].is_unique),
    check("status counts match Sheet1 (Success=63,967)",
          (df["booking_status"] == "Success").sum() == 63_967),
    check("all dates fall in July 2024",
          df["booking_datetime"].min().month == 7 and df["booking_datetime"].max().month == 7),
    check("success rows all have payment method + ratings",
          df.loc[df.is_success == 1, ["payment_method", "driver_rating", "customer_rating"]]
            .notna().all().all()),
    check("non-success rows have no payment method / ratings",
          df.loc[df.is_success == 0, ["payment_method", "driver_rating", "customer_rating"]]
            .isna().all().all()),
    check("non-success rows have ride_distance = 0",
          (df.loc[df.is_success == 0, "ride_distance"] == 0).all()),
    check("ratings are between 1 and 5",
          df[["driver_rating", "customer_rating"]].stack().dropna().between(1, 5).all()),
    check("booking_value has no zero / negative values", (df["booking_value"] > 0).all()),
]

# --------------------------------------------------------------------------
# 8. EXPORT
# --------------------------------------------------------------------------
final_cols = [
    "booking_id", "booking_datetime", "booking_date", "booking_time", "booking_hour",
    "day_name", "day_of_week", "is_weekend", "time_slot",
    "customer_id", "vehicle_type", "pickup_location", "drop_location",
    "booking_status", "is_success", "cancel_type",
    "customer_cancel_reason", "driver_cancel_reason",
    "incomplete_ride", "incomplete_reason",
    "v_tat", "c_tat", "booking_value", "payment_method", "ride_distance",
    "driver_rating", "customer_rating", "vehicle_image_url",
]
df = df[final_cols]
df.to_csv(OUTPUT_FILE, index=False)

print(f"\nSaved {len(df):,} rows x {df.shape[1]} columns -> {OUTPUT_FILE}")
print("All checks passed." if all(results) else "WARNING: some checks failed - review above.")
print("\nPreview:")
print(df.head(3).T)