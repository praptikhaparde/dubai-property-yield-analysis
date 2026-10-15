-- Price per sqft and gross yield by area and year (same-year comparison)
WITH s AS (
    SELECT area_id, MAX(area_name_en) AS area,
           strftime('%Y', instance_date) AS yr,
           COUNT(*) AS sales_deals, AVG(price_per_sqft) AS price_sqft
    FROM sales
    WHERE property_sub_type_en = 'Flat' AND reg_type_en = 'Existing Properties'
    GROUP BY area_id, yr HAVING sales_deals >= 30
),
r AS (
    SELECT area_id, strftime('%Y', contract_start_date) AS yr,
           COUNT(*) AS rent_deals, AVG(rent_per_sqft) AS rent_sqft
    FROM rent
    WHERE ejari_property_type_en = 'Flat' AND contract_reg_type_en = 'New'
    GROUP BY area_id, yr HAVING rent_deals >= 30
)
SELECT s.area, s.yr, s.sales_deals, r.rent_deals,
       ROUND(s.price_sqft) AS price_per_sqft,
       ROUND(r.rent_sqft, 1) AS rent_per_sqft,
       ROUND(100.0 * r.rent_sqft / s.price_sqft, 1) AS gross_yield_pct
FROM s JOIN r ON s.area_id = r.area_id AND s.yr = r.yr
ORDER BY s.area, s.yr;
