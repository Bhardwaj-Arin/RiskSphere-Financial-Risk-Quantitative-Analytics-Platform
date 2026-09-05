# Validation Report — parametric_var

## Purpose
One-day portfolio VaR/ES model in the RiskQuant educational risk workflow.

## Backtesting
Forecasts: 2358; exceptions: 34; Kupiec p=0.043087; Christoffersen p=0.097725.

## Interpretation
A p-value above the configured threshold means the test did not reject its null; it does not prove the model is correct.

## Stability by period
      model_id period_end  n_forecasts  n_exceptions  exception_rate  avg_var  realized_loss_std
parametric_var 2015-12-31           10             0        0.000000 0.016190           0.004358
parametric_var 2016-12-31          261             4        0.015326 0.015585           0.006663
parametric_var 2017-12-31          260             3        0.011538 0.015643           0.005980
parametric_var 2018-12-31          261             2        0.007663 0.013530           0.005497
parametric_var 2019-12-31          261             3        0.011494 0.011827           0.005294
parametric_var 2020-12-31          262             5        0.019084 0.011828           0.005034
parametric_var 2021-12-31          261             2        0.007663 0.012466           0.005554
parametric_var 2022-12-31          260             8        0.030769 0.014016           0.007643
parametric_var 2023-12-31          260             1        0.003846 0.017554           0.006821
parametric_var 2024-12-31          262             6        0.022901 0.014080           0.006138

## Scope limitation
Educational risk-factor prototype; not regulatory model approval or production validation.