DROP VIEW IF EXISTS vw_abc_analysis;

CREATE VIEW vw_abc_analysis AS
WITH calibration_usage AS (
    SELECT
        p.part_id,
        p.part_name,
        p.category,
        p.ved_class,
        p.unit_cost,
        COALESCE(SUM(d.demand_qty), 0) / 2.0 AS annual_demand_qty,
        (COALESCE(SUM(d.demand_qty), 0) / 2.0) * p.unit_cost AS annual_usage_value
    FROM parts p
    LEFT JOIN demand_history d
        ON p.part_id = d.part_id AND d.is_backtest = 0
    GROUP BY p.part_id, p.part_name, p.category, p.ved_class, p.unit_cost
),
ranked_usage AS (
    SELECT
        *,
        SUM(annual_usage_value) OVER (
            ORDER BY annual_usage_value DESC, part_id ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_value,
        SUM(annual_usage_value) OVER () AS total_portfolio_value
    FROM calibration_usage
)
SELECT
    part_id,
    part_name,
    category,
    ved_class,
    ROUND(unit_cost, 2) AS unit_cost,
    ROUND(annual_demand_qty, 2) AS annual_demand_qty,
    ROUND(annual_usage_value, 2) AS annual_usage_value,
    ROUND(cumulative_value / NULLIF(total_portfolio_value, 0), 4) AS cumulative_share,
    CASE
        WHEN (cumulative_value / NULLIF(total_portfolio_value, 0)) <= 0.80 THEN 'A'
        WHEN (cumulative_value / NULLIF(total_portfolio_value, 0)) <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM ranked_usage;
