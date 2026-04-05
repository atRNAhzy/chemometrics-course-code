from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor



def split_data(
    df: pd.DataFrame,
    test_size: float,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X = df.drop(columns=["quality"])
    y = df["quality"]
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )



def build_preprocessor(feature_columns: pd.Index) -> ColumnTransformer:
    numeric_cols = [c for c in feature_columns if c != "wine_type"]
    categorical_cols = ["wine_type"]

    numeric_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        [
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )



def train_regressors(preprocessor: ColumnTransformer, random_state: int) -> Dict[str, Pipeline]:
    models = {
        "ridge": Ridge(alpha=1.0),
        "rf": RandomForestRegressor(
            n_estimators=900,
            max_depth=28,
            min_samples_leaf=1,
            max_features="sqrt",
            random_state=random_state,
            n_jobs=2,
        ),
        "hgb": HistGradientBoostingRegressor(
            learning_rate=0.03,
            max_depth=None,
            max_leaf_nodes=63,
            min_samples_leaf=20,
            l2_regularization=0.1,
            max_iter=900,
            random_state=random_state,
        ),
    }

    return {
        name: Pipeline([("prep", preprocessor), ("model", model)])
        for name, model in models.items()
    }



def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }



def train_tier_classifier(
    preprocessor: ColumnTransformer,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> Dict[str, float]:
    y_train_bin = (y_train >= 7).astype(int)
    y_test_bin = (y_test >= 7).astype(int)

    clf = Pipeline(
        [
            ("prep", preprocessor),
            (
                "model",
                LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs"),
            ),
        ]
    )
    clf.fit(X_train, y_train_bin)
    proba = clf.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    return {
        "accuracy": float(accuracy_score(y_test_bin, pred)),
        "f1": float(f1_score(y_test_bin, pred)),
        "roc_auc": float(roc_auc_score(y_test_bin, proba)),
    }
