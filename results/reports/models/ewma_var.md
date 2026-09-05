# Validation Report — ewma_var

## Purpose
One-day portfolio VaR/ES model in the RiskQuant educational risk workflow.

## Backtesting
Forecasts: 2358; exceptions: 34; Kupiec p=0.043087; Christoffersen p=0.097725.

## Interpretation
A p-value above the configured threshold means the test did not reject its null; it does not prove the model is correct.

## Stability by period
model_id period_end  n_forecasts  n_exceptions  exception_rate  avg_var  realized_loss_std
ewma_var 2015-12-31           10             0        0.000000 0.020393           0.004358
ewma_var 2016-12-31          261             4        0.015326 0.014648           0.006663
ewma_var 2017-12-31          260             5        0.019231 0.013542           0.005980
ewma_var 2018-12-31          261             3        0.011494 0.012962           0.005497
ewma_var 2019-12-31          261             4        0.015326 0.011762           0.005294
ewma_var 2020-12-31          262             6        0.022901 0.011554           0.005034
ewma_var 2021-12-31          261             2        0.007663 0.012772           0.005554
ewma_var 2022-12-31          260             3        0.011538 0.016037           0.007643
ewma_var 2023-12-31          260             2        0.007692 0.015470           0.006821
ewma_var 2024-12-31          262             5        0.019084 0.013206           0.006138

## Scope limitation
Educational risk-factor prototype; not regulatory model approval or production validation.