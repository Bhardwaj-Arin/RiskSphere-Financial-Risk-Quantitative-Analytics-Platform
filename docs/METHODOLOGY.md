# Risk Methodology

## Market return representation

Price-like factors use simple percentage returns. `RATES_10Y` is represented as an absolute decimal yield change. When `portfolio.mapping.apply_rate_duration=true`, the rate move is converted to a bond-return proxy using

`ΔP/P ≈ -D·Δy + 0.5·C·(Δy)^2`.

DV01 is reported as the first-order currency sensitivity `Notional × Duration × 0.0001`.

## VaR and Expected Shortfall

All market forecasts are one-step-ahead and out-of-sample. Historical VaR uses the empirical lower quantile of the trailing training window. Parametric VaR uses the trailing mean and standard deviation with a normal quantile. EWMA uses a recursive conditional variance with configured decay. GARCH(1,1) is a challenger fitted by Gaussian quasi-maximum likelihood on the initial training window and then updated recursively out-of-sample.

Expected Shortfall is reported as average historical tail loss for Historical VaR and the corresponding conditional-normal tail expectation for Parametric/EWMA/GARCH models.

## Backtesting

An exception occurs when realized loss exceeds the VaR forecast. Kupiec tests whether exception frequency is consistent with the target rate. Christoffersen tests first-order independence of exceptions. The dashboard and reports keep these two interpretations separate.

## Stress and reverse stress

Configured factor shocks are mapped through the same portfolio exposure logic used by the portfolio engine. Reverse stress solves for a minimum-L2-norm shock vector that reaches the configured target loss within factor bounds. This is a constrained scenario under the model, not a claim of the uniquely true market worst case.

## Credit Expected Loss

PD is estimated with a Logistic Regression baseline and XGBoost challenger. Holdout metrics include ROC-AUC, KS, Brier score, calibration and segment performance. Expected Loss is

`EL = PD × LGD × EAD`.

LGD and EAD are deliberately transparent simplified assumptions/proxies in this educational implementation. Credit stress scales PD and shifts LGD under configured scenarios.

## Monitoring and governance

PSI compares reference and current distributions. Risk limits report value, limit, utilization and status. Model inventory records purpose, target, data, assumptions, limitations, version and validation status. Findings are triggered from backtesting, drift and limit rules.
