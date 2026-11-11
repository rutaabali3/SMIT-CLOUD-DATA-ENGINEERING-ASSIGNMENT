-- Question 3: Top 5 riders by total COD shortfall
SELECT TOP 5
    p.rider_id,
    SUM(p.cod_due) AS total_cod_due,
    SUM(COALESCE(r.amount, 0)) AS total_remitted,
    SUM(p.cod_due - COALESCE(r.amount, 0)) AS total_shortfall
FROM clean.parcel_final p
LEFT JOIN clean.remittances r ON p.parcel_id = r.parcel_id
GROUP BY p.rider_id
ORDER BY total_shortfall DESC;
