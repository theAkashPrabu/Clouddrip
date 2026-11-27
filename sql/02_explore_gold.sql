-- Spend by environment, split weekday vs weekend
SELECT
    r.environment,
    CASE WHEN d.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(DISTINCT r.resource_key)        AS resources,
    CAST(SUM(f.billed_cost_gbp) AS DECIMAL(12,2)) AS cost_gbp
FROM dbo.fact_daily_cost AS f
JOIN dbo.dim_resource    AS r ON r.resource_key = f.resource_key
JOIN dbo.dim_date        AS d ON d.date_key     = f.date_key
GROUP BY r.environment, d.is_weekend
ORDER BY r.environment, day_type;