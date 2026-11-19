-- ============================================================
-- Ola Ride Insights - Step 3b: SQL queries (MySQL)
-- Table: ola_db.ola_rides  (103,024 rows)
-- ============================================================
USE ola_db;


-- ------------------------------------------------------------
-- Q1. Retrieve all successful bookings
-- Expected: 63,967 rows
-- ------------------------------------------------------------
SELECT *
FROM ola_rides
WHERE booking_status = 'Success';


-- ------------------------------------------------------------
-- Q2. Average ride distance for each vehicle type
-- Successful rides only: cancelled rides have distance 0 and
-- would drag the averages down (Sheet1's pivot included them).
-- Expected: Auto 10.04 | Bike 24.93 | Mini 24.98 | Prime Plus 25.03
--           Prime SUV 24.88 | Prime Sedan 25.01 | eBike 25.15
-- ------------------------------------------------------------
SELECT vehicle_type,
       ROUND(AVG(ride_distance), 2) AS avg_ride_distance_km
FROM ola_rides
WHERE booking_status = 'Success'
GROUP BY vehicle_type
ORDER BY avg_ride_distance_km DESC;


-- ------------------------------------------------------------
-- Q3. Total number of rides cancelled by customers
-- Expected: 10,499
-- ------------------------------------------------------------
SELECT COUNT(*) AS cancelled_by_customers
FROM ola_rides
WHERE booking_status = 'Canceled by Customer';


-- ------------------------------------------------------------
-- Q4. Top 5 customers by number of rides booked
-- Many customers tie (26 customers have 4 rides), so total
-- booking value is used as a tie-breaker to keep it deterministic.
-- Expected: CID954071 (5) | CID836942 (4) | CID387617 (4)
--           CID309168 (4) | CID635963 (4)
-- ------------------------------------------------------------
SELECT customer_id,
       COUNT(*)           AS total_rides,
       SUM(booking_value) AS total_booking_value
FROM ola_rides
GROUP BY customer_id
ORDER BY total_rides DESC, total_booking_value DESC
LIMIT 5;


-- ------------------------------------------------------------
-- Q5. Rides cancelled by drivers for personal and car-related issues
-- Expected: 6,542
-- ------------------------------------------------------------
SELECT COUNT(*) AS driver_cancels_personal_car_issue
FROM ola_rides
WHERE driver_cancel_reason = 'Personal & Car related issue';


-- ------------------------------------------------------------
-- Q6. Maximum and minimum driver ratings for Prime Sedan bookings
-- Expected: max 5.0 | min 3.0
-- ------------------------------------------------------------
SELECT MAX(driver_rating) AS max_driver_rating,
       MIN(driver_rating) AS min_driver_rating
FROM ola_rides
WHERE vehicle_type = 'Prime Sedan';


-- ------------------------------------------------------------
-- Q7. All rides where payment was made using UPI
-- Expected: 25,881 rows
-- ------------------------------------------------------------
SELECT *
FROM ola_rides
WHERE payment_method = 'UPI';


-- ------------------------------------------------------------
-- Q8. Average customer rating per vehicle type
-- (NULL ratings of cancelled rides are ignored by AVG automatically)
-- Expected: Auto 4.00 | Bike 3.99 | Mini 4.00 | Prime Plus 4.01
--           Prime SUV 4.00 | Prime Sedan 4.00 | eBike 3.99
-- ------------------------------------------------------------
SELECT vehicle_type,
       ROUND(AVG(customer_rating), 2) AS avg_customer_rating
FROM ola_rides
GROUP BY vehicle_type
ORDER BY avg_customer_rating DESC;


-- ------------------------------------------------------------
-- Q9. Total booking value of rides completed successfully
-- Expected: 35,080,467
-- ------------------------------------------------------------
SELECT SUM(booking_value) AS total_booking_value_successful
FROM ola_rides
WHERE booking_status = 'Success';


-- ------------------------------------------------------------
-- Q10. All incomplete rides along with the reason
-- Incomplete rides sit inside the 'Success' status, flagged by
-- incomplete_ride = 'Yes'.
-- Expected: 3,926 rows (Customer Demand 1,601 | Vehicle Breakdown 1,591
--           | Other Issue 734)
-- ------------------------------------------------------------
SELECT booking_id,
       booking_date,
       customer_id,
       vehicle_type,
       booking_status,
       incomplete_reason
FROM ola_rides
WHERE incomplete_ride = 'Yes';