-- Question 4: Parcels with a remittance but a final status that is not delivered
SELECT
    p.parcel_id,
    p.rider_id,
    p.zone,
    p.final_status,
    p.cod_amount,
    r.remittance_id,
    r.amount AS remitted_amount,
    r.remitted_at
FROM clean.parcel_final p
JOIN clean.remittances r ON p.parcel_id = r.parcel_id
WHERE p.final_status <> 'delivered'
ORDER BY p.parcel_id;
