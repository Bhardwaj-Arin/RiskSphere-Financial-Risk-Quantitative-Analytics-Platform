-- RiskSphere example PostgreSQL analysis queries.

-- 1) Latest completed run using a CTE.
WITH latest_run AS (
    SELECT run_id
    FROM model_runs
    WHERE status = 'COMPLETED'
    ORDER BY executed_at DESC
    LIMIT 1
)
SELECT * FROM model_runs WHERE run_id = (SELECT run_id FROM latest_run);

-- 2) Latest VaR / ES per model for a portfolio using a window function.
WITH latest_run AS (
    SELECT run_id FROM model_runs WHERE status='COMPLETED'
    ORDER BY executed_at DESC LIMIT 1
), ranked AS (
    SELECT r.*,
           ROW_NUMBER() OVER (PARTITION BY r.model_id ORDER BY r.forecast_date DESC) AS rn
    FROM risk_results r
    JOIN latest_run lr ON r.run_id = lr.run_id
    WHERE r.portfolio_id = :portfolio_id
)
SELECT model_id, forecast_date, var, expected_shortfall, exception_flag
FROM ranked
WHERE rn = 1
ORDER BY model_id;

-- 3) Exception rate per model in the latest run.
WITH latest_run AS (
    SELECT run_id FROM model_runs WHERE status='COMPLETED'
    ORDER BY executed_at DESC LIMIT 1
)
SELECT b.model_id,
       SUM(CASE WHEN b.exception_flag THEN 1 ELSE 0 END) AS n_exceptions,
       COUNT(*) AS n_forecasts,
       AVG(CASE WHEN b.exception_flag THEN 1.0 ELSE 0.0 END) AS exception_rate
FROM backtest_results b
JOIN latest_run lr ON b.run_id = lr.run_id
GROUP BY b.model_id
ORDER BY b.model_id;

-- 4) Stress scenario ranking.
WITH latest_run AS (
    SELECT run_id FROM model_runs WHERE status='COMPLETED'
    ORDER BY executed_at DESC LIMIT 1
)
SELECT s.scenario_id, MAX(s.portfolio_loss) AS portfolio_loss
FROM stress_results s
JOIN latest_run lr ON s.run_id = lr.run_id
GROUP BY s.scenario_id
ORDER BY portfolio_loss DESC;

-- 5) Credit Expected Loss by segment.
WITH latest_run AS (
    SELECT run_id FROM model_runs WHERE status='COMPLETED'
    ORDER BY executed_at DESC LIMIT 1
)
SELECT COALESCE(c.segment, 'UNSEGMENTED') AS segment,
       SUM(c.ead) AS total_ead,
       SUM(c.expected_loss) AS expected_loss,
       SUM(c.expected_loss) / NULLIF(SUM(c.ead), 0) AS expected_loss_rate,
       AVG(c.pd) AS mean_pd
FROM credit_predictions c
JOIN latest_run lr ON c.run_id = lr.run_id
GROUP BY COALESCE(c.segment, 'UNSEGMENTED')
ORDER BY expected_loss DESC;

-- 6) Risk limit breaches and warnings.
WITH latest_run AS (
    SELECT run_id FROM model_runs WHERE status='COMPLETED'
    ORDER BY executed_at DESC LIMIT 1
)
SELECT l.metric, l.value, l.limit_value, l.utilization, l.status
FROM risk_limits l
JOIN latest_run lr ON l.run_id = lr.run_id
WHERE l.status IN ('WARNING', 'BREACH')
ORDER BY l.utilization DESC;
