-- Question 2: On-time delivery rate by zone
SELECT
    zone,
    COUNT(*) AS total_parcels,
    SUM(CASE WHEN final_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_parcels,
    SUM(on_time) AS on_time_deliveries,
    ROUND(100.0 * SUM(on_time) / NULLIF(SUM(CASE WHEN final_status = 'delivered' THEN 1 ELSE 0 END), 0), 2) AS on_time_delivery_rate_pct
FROM clean.parcel_final
GROUP BY zone
ORDER BY zone;
