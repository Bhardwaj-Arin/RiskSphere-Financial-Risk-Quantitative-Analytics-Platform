"""Credit PD baseline/challenger modelling with calibration metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.calibration import calibration_curve


@dataclass
class CreditRun:
    predictions: pd.DataFrame
    metrics: pd.DataFrame
    calibration: pd.DataFrame
    models: dict[str, Any]
    feature_columns: list[str]


def _split(df: pd.DataFrame, target: str, test_fraction: float, seed: int,
           observation_date_column: str | None) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if observation_date_column and observation_date_column in df.columns:
        ordered = df.sort_values(observation_date_column).reset_index(drop=True)
        cut = int(len(ordered) * (1 - test_fraction))
        return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy(), "chronological"
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    cut = int(len(df) * (1 - test_fraction))
    return df.iloc[idx[:cut]].copy(), df.iloc[idx[cut:]].copy(), "random"


def _preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric = X.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    num_pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    cat_pipe = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                         ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("num", num_pipe, numeric), ("cat", cat_pipe, categorical)], remainder="drop")


def _metric_row(model_id: str, y: pd.Series, pd_hat: np.ndarray, split_type: str) -> dict:
    auc = roc_auc_score(y, pd_hat) if y.nunique() > 1 else float("nan")
    ks = ks_2samp(pd_hat[y.to_numpy() == 1], pd_hat[y.to_numpy() == 0]).statistic if y.nunique() > 1 else float("nan")
    return {
        "model_id": model_id,
        "roc_auc": float(auc),
        "ks": float(ks),
        "brier_score": float(brier_score_loss(y, pd_hat)),
        "mean_predicted_pd": float(np.mean(pd_hat)),
        "observed_default_rate": float(np.mean(y)),
        "split_type": split_type,
    }


def _calibration_rows(model_id: str, y: pd.Series, pd_hat: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    frac, mean = calibration_curve(y, pd_hat, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame({"model_id": model_id, "mean_predicted_pd": mean, "observed_default_rate": frac})


def train_pd_models(df: pd.DataFrame, config: dict) -> CreditRun:
    ccfg = config["credit"]
    target = ccfg.get("target_column", "default_flag")
    ead_col = ccfg.get("ead_column", "ead")
    date_col = ccfg.get("observation_date_column", "observation_date")
    excluded = {target, ead_col, "source"}
    if date_col in df.columns:
        excluded.add(date_col)
    # Do not leak direct loan amount twice when EAD is derived from it only if the
    # user explicitly supplies EAD. Here loan_amount remains a legitimate feature.
    feature_cols = [c for c in df.columns if c not in excluded]

    train, test, split_type = _split(df, target, float(ccfg.get("test_fraction", 0.25)), int(ccfg.get("seed", 123)), date_col)
    X_train, y_train = train[feature_cols], train[target].astype(int)
    X_test, y_test = test[feature_cols], test[target].astype(int)

    logistic = Pipeline([
        ("prep", _preprocessor(X_train)),
        ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=int(ccfg.get("seed", 123)))),
    ])
    logistic.fit(X_train, y_train)

    models: dict[str, Any] = {"logistic_pd": logistic}
    pred_map: dict[str, np.ndarray] = {"logistic_pd": logistic.predict_proba(X_test)[:, 1]}

    if str(ccfg.get("challenger", "xgboost")).lower() == "xgboost":
        try:
            from xgboost import XGBClassifier
            xgb = Pipeline([
                ("prep", _preprocessor(X_train)),
                ("model", XGBClassifier(
                    n_estimators=180, max_depth=3, learning_rate=0.04,
                    subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
                    random_state=int(ccfg.get("seed", 123)), n_jobs=2,
                )),
            ])
            xgb.fit(X_train, y_train)
            models["xgboost_pd"] = xgb
            pred_map["xgboost_pd"] = xgb.predict_proba(X_test)[:, 1]
        except ImportError:
            pass

    base_cols = []
    if date_col in test.columns:
        base_cols.append(date_col)
    base_cols += [target, ead_col]
    if "segment" in test.columns:
        base_cols.append("segment")
    predictions = test[base_cols].copy().reset_index(drop=True)
    metrics, cal = [], []
    for model_id, pd_hat in pred_map.items():
        predictions[f"pd_{model_id}"] = pd_hat
        metrics.append(_metric_row(model_id, y_test.reset_index(drop=True), pd_hat, split_type))
        cal.append(_calibration_rows(model_id, y_test.reset_index(drop=True), pd_hat))

    return CreditRun(
        predictions=predictions,
        metrics=pd.DataFrame(metrics),
        calibration=pd.concat(cal, ignore_index=True),
        models=models,
        feature_columns=feature_cols,
    )
