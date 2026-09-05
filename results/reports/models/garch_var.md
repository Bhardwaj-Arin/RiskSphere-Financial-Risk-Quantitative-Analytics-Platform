# Validation Report — garch_var

## Purpose
One-day portfolio VaR/ES model in the RiskQuant educational risk workflow.

## Backtesting
Forecasts: 2358; exceptions: 22; Kupiec p=0.740845; Christoffersen p=0.519660.

## Interpretation
A p-value above the configured threshold means the test did not reject its null; it does not prove the model is correct.

## Stability by period
 model_id period_end  n_forecasts  n_exceptions  exception_rate  avg_var  realized_loss_std
garch_var 2015-12-31           10             0        0.000000 0.014739           0.004358
garch_var 2016-12-31          261             2        0.007663 0.015483           0.006663
garch_var 2017-12-31          260             4        0.015385 0.015076           0.005980
garch_var 2018-12-31          261             3        0.011494 0.014986           0.005497
garch_var 2019-12-31          261             2        0.007663 0.014371           0.005294
garch_var 2020-12-31          262             1        0.003817 0.014435           0.005034
garch_var 2021-12-31          261             2        0.007663 0.014979           0.005554
garch_var 2022-12-31          260             1        0.003846 0.016363           0.007643
garch_var 2023-12-31          260             2        0.007692 0.015684           0.006821
garch_var 2024-12-31          262             5        0.019084 0.014967           0.006138

## Scope limitation
Educational risk-factor prototype; not regulatory model approval or production validation.