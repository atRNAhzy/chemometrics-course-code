from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from autogluon.tabular import TabularPredictor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results" / "autogluon_30min_v2"
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    red = pd.read_csv(ROOT / "data" / "winequality-red.csv", sep=";")
    white = pd.read_csv(ROOT / "data" / "winequality-white.csv", sep=";")
    red["wine_type"] = "red"
    white["wine_type"] = "white"
    df = pd.concat([red, white], ignore_index=True)
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)


def main() -> None:
    df = load_data()
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["quality"],
    )

    predictor = TabularPredictor(
        label="quality",
        problem_type="regression",
        eval_metric="r2",
        path=str(RESULT_DIR / "models"),
        verbosity=2,
    )

    # 参考该数据集常见高分结构：GBM / CAT / XGB + 多层堆叠集成
    predictor.fit(
        train_data=train_df,
        presets="best_quality",
        time_limit=30 * 60,
        num_bag_folds=8,
        num_stack_levels=2,
        num_bag_sets=1,
        dynamic_stacking=True,
        hyperparameters={
            "GBM": [{}, {"extra_trees": True, "ag_args": {"name_suffix": "XT"}}],
            "CAT": [{}],
            "XGB": [{}],
            "RF": [{"criterion": "squared_error", "ag_args": {"name_suffix": "MSE"}}],
            "XT": [{"criterion": "squared_error", "ag_args": {"name_suffix": "MSE"}}],
            "NN_TORCH": {},
        },
    )

    leaderboard = predictor.leaderboard(test_df, silent=True)
    leaderboard.to_csv(RESULT_DIR / "leaderboard.csv", index=False)

    y_true = test_df["quality"].to_numpy()
    y_pred = predictor.predict(test_df.drop(columns=["quality"]))
    metrics = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "best_model": str(predictor.model_best),
        "rows": int(len(df)),
    }

    (RESULT_DIR / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pred_df = test_df[["quality"]].rename(columns={"quality": "y_true"}).copy()
    pred_df["y_pred"] = np.round(np.asarray(y_pred), 4)
    pred_df["abs_error"] = np.round(np.abs(pred_df["y_true"] - pred_df["y_pred"]), 4)
    pred_df.to_csv(RESULT_DIR / "predictions.csv", index=False)

    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
