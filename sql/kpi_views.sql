DROP VIEW IF EXISTS vw_part_kpis;

CREATE VIEW vw_part_kpis AS
WITH lt_stats AS (
    SELECT
        part_id,
        COUNT(*) AS shipment_count,
        ROUND(AVG(lead_time_days), 2) AS avg_lead_time_days,
        MIN(lead_time_days) AS min_lead_time_days,
        MAX(lead_time_days) AS max_lead_time_days
    FROM lead_time_history
    GROUP BY part_id
)
SELECT
    a.part_id,
    a.part_name,
    a.category,
    a.ved_class,
    a.abc_class,
    a.unit_cost,
    a.annual_demand_qty,
    a.annual_usage_value,
    cp.min_stock,
    cp.max_stock,
    cp.initial_stock,
    lt.avg_lead_time_days,
    lt.max_lead_time_days,
    ROUND((cp.min_stock * a.unit_cost), 2) AS min_stock_capital_tl
FROM vw_abc_analysis a
JOIN current_policy cp ON a.part_id = cp.part_id
JOIN lt_stats lt ON a.part_id = lt.part_id;
