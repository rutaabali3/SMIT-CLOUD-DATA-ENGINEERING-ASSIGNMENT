-- Question 5: Delivered COD parcels with no remittance — count and total rupees at risk
SELECT
    COUNT(*) AS delivered_cod_parcels_without_remittance,
    SUM(p.cod_due) AS total_rupees_at_risk
FROM clean.parcel_final p
LEFT JOIN clean.remittances r ON p.parcel_id = r.parcel_id
WHERE p.final_status = 'delivered'
  AND p.cod_due > 0
  AND r.parcel_id IS NULL;
