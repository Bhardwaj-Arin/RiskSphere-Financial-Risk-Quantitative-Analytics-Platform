# RiskForge-QRM Model Validation Report

Generated: 2026-09-05T10:15:30.126866Z

**Scope statement:** Educational prototype. Not a production risk engine. Not a claim of Basel/regulatory compliance.

## 1. Model objective
Estimate and validate market risk, quantify stress/reverse-stress losses, attribute risk, and extend the educational workflow into credit expected loss and monitoring.

## 2. Data
Market source=synthetic, version=e67c9d9daacd0157, rows=13045. Credit source=synthetic.

## 3. Assumptions
99% one-day VaR; 250-observation training window; explicit rate duration mapping; linear factor portfolio approximation; simplified credit LGD/EAD.

## 4. Implementation
Historical, parametric, EWMA and GARCH challenger VaR/ES; Kupiec/Christoffersen; stress/reverse stress; attribution; credit PD baseline/challenger; SQL persistence; limits and PSI monitoring.

## 5. Test design
Strict out-of-sample market forecasts plus statistical coverage/independence tests. Credit holdout is chronological where dates exist. SQL results are reconciled to Python in-memory totals.

## 6. Results
      model_id  n_forecasts  n_exceptions  exception_rate  target_rate  avg_exceedance_size  avg_var
      ewma_var         2358            34        0.014419         0.01             0.004121 0.013576
     garch_var         2358            22        0.009330         0.01             0.003648 0.015147
historical_var         2358            32        0.013571         0.01             0.004000 0.014738
parametric_var         2358            34        0.014419         0.01             0.003998 0.014065

Limits:
              metric    value  limit  utilization status
              var_99 0.022812   0.04     0.570294     OK
               es_99 0.026095   0.06     0.434917     OK
         stress_loss 0.089950   0.20     0.449750     OK
credit_expected_loss 0.072371   0.04     1.809286 BREACH

## 7. Failures / exceptions observed
ewma_var: backtest rule did not pass (Kupiec p=0.04309, Christoffersen p=0.09773).
parametric_var: backtest rule did not pass (Kupiec p=0.04309, Christoffersen p=0.09773).

## 8. Limitations
Educational risk-factor prototype; simplified portfolio mapping and fixed-income approximation; synthetic default datasets in offline mode; GARCH uses Gaussian QMLE; credit target/LGD/EAD are simplified and data-dependent.

## 9. Conclusion
Results must be interpreted model-by-model. Passing a test does not prove a model is correct; failing a test identifies an assumption/performance issue requiring review.

## 10. Recommended next steps
Use sourced real market/credit data, review model assumptions, run PostgreSQL deployment mode, and document dataset-specific limitations.