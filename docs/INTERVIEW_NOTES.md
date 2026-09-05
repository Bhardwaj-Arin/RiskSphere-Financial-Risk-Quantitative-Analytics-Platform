# RiskSphere — Interview Notes

## Explain the project in one sentence

RiskSphere is an educational end-to-end financial-risk analytics platform covering market VaR/ES, backtesting, stress and reverse stress, factor attribution, simplified credit Expected Loss, model monitoring, limits, SQL persistence, and Streamlit reporting.

## The backtesting result should not be oversold

In the current synthetic RiskSphere run, Historical VaR and the GARCH challenger do not fail either 5% test. Parametric and EWMA VaR fail the **Kupiec unconditional-coverage test** at 5% while their **Christoffersen independence tests do not reject independence**.

That means the current finding is about exception frequency, not demonstrated exception clustering. Say this precisely.

Do not say:

> "Christoffersen proved the EWMA model clusters exceptions."

Instead say:

> "In this run EWMA had a higher-than-target exception rate and Kupiec rejected the target coverage at 5%, while Christoffersen did not reject exception independence. I therefore treat coverage as a model-validation finding and would review volatility/tail assumptions rather than declaring the model correct or broken from one statistic."

## Why the old baseline changed

The original project treated the 10-year rate change directly inside the weighted return mapping. RiskSphere can map absolute yield changes through duration/convexity. The default configuration enables this more realistic rate approximation, so some VaR/backtesting numbers change. This is expected and documented.

## GARCH is a challenger, not an automatic winner

The current synthetic run gives favorable GARCH backtesting statistics, but that does not establish general superiority. A model comparison is dataset-, horizon-, parameter-, and regime-dependent.

## Credit-risk wording

The default credit dataset is synthetic and is included for offline reproducibility. Do not call its ROC-AUC, PD, Expected Loss, or stress results bank portfolio results. Explain Logistic Regression as the transparent baseline and XGBoost as a challenger. Compare discrimination and calibration rather than choosing a winner only from ROC-AUC.

## SQL wording

The code has a SQLAlchemy repository and PostgreSQL-ready schema. The default offline run uses SQLite when no `RISKQUANT_DATABASE_URL` is supplied. Say "PostgreSQL-supported" unless you actually run it against PostgreSQL.

## Governance wording

Limits, PSI, model inventory, and validation findings are educational governance controls. They demonstrate lifecycle thinking but are not a regulatory model-risk-management framework.
