-- ============================================================
-- Ola Ride Insights - Step 3a: Create database and table
-- Run this in MySQL Workbench BEFORE loading the data.
-- ============================================================

CREATE DATABASE IF NOT EXISTS ola_db;
USE ola_db;

DROP TABLE IF EXISTS ola_rides;

CREATE TABLE ola_rides (
    booking_id              VARCHAR(20)   NOT NULL,
    booking_datetime        DATETIME      NOT NULL,
    booking_date            DATE          NOT NULL,
    booking_time            TIME          NOT NULL,
    booking_hour            TINYINT       NOT NULL,
    day_name                VARCHAR(10)   NOT NULL,
    day_of_week             TINYINT       NOT NULL,      -- 1 = Monday ... 7 = Sunday
    is_weekend              VARCHAR(7)    NOT NULL,      -- 'Weekday' / 'Weekend'
    time_slot               VARCHAR(25)   NOT NULL,
    customer_id             VARCHAR(15)   NOT NULL,
    vehicle_type            VARCHAR(20)   NOT NULL,
    pickup_location         VARCHAR(50)   NOT NULL,
    drop_location           VARCHAR(50)   NOT NULL,
    booking_status          VARCHAR(25)   NOT NULL,
    is_success              TINYINT       NOT NULL,      -- 1 = Success, 0 = otherwise
    cancel_type             VARCHAR(15)   NOT NULL,      -- Customer / Driver / Not Cancelled
    customer_cancel_reason  VARCHAR(60)   NULL,
    driver_cancel_reason    VARCHAR(60)   NULL,
    incomplete_ride         VARCHAR(3)    NULL,          -- Yes / No (only for Success rows)
    incomplete_reason       VARCHAR(30)   NULL,
    v_tat                   INT           NULL,
    c_tat                   INT           NULL,
    booking_value           INT           NOT NULL,
    payment_method          VARCHAR(20)   NULL,
    ride_distance           INT           NOT NULL,
    driver_rating           DECIMAL(2,1)  NULL,
    customer_rating         DECIMAL(2,1)  NULL,
    vehicle_image_url       VARCHAR(255)  NULL,
    PRIMARY KEY (booking_id),
    INDEX idx_customer (customer_id),
    INDEX idx_vehicle  (vehicle_type),
    INDEX idx_status   (booking_status),
    INDEX idx_date     (booking_date)
);

-- Table should now exist and be empty:
SELECT COUNT(*) AS rows_in_table FROM ola_rides;   -- expect 0