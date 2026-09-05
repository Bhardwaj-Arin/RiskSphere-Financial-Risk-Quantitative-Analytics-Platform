# Validation Report — historical_var

## Purpose
One-day portfolio VaR/ES model in the RiskQuant educational risk workflow.

## Backtesting
Forecasts: 2358; exceptions: 32; Kupiec p=0.098358; Christoffersen p=0.076620.

## Interpretation
A p-value above the configured threshold means the test did not reject its null; it does not prove the model is correct.

## Stability by period
      model_id period_end  n_forecasts  n_exceptions  exception_rate  avg_var  realized_loss_std
historical_var 2015-12-31           10             0        0.000000 0.017220           0.004358
historical_var 2016-12-31          261             3        0.011494 0.017713           0.006663
historical_var 2017-12-31          260             3        0.011538 0.018393           0.005980
historical_var 2018-12-31          261             1        0.003831 0.016097           0.005497
historical_var 2019-12-31          261             4        0.015326 0.010831           0.005294
historical_var 2020-12-31          262             4        0.015267 0.012655           0.005034
historical_var 2021-12-31          261             2        0.007663 0.012761           0.005554
historical_var 2022-12-31          260             8        0.030769 0.013271           0.007643
historical_var 2023-12-31          260             1        0.003846 0.017011           0.006821
historical_var 2024-12-31          262             6        0.022901 0.013844           0.006138

## Scope limitation
Educational risk-factor prototype; not regulatory model approval or production validation.