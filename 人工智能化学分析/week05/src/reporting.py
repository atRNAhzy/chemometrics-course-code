from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline


def _base_style() -> None:
    plt.style.use("tableau-colorblind10")


def save_metrics(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def save_predictions(path: Path, y_true: pd.Series, y_pred: np.ndarray) -> None:
    df = pd.DataFrame({"y_true": y_true, "y_pred": np.round(y_pred, 3)})
    df["abs_error"] = (df["y_true"] - df["y_pred"]).abs().round(3)
    df.to_csv(path, index=False)


def save_scatter_plot(path: Path, y_true: pd.Series, y_pred: np.ndarray) -> None:
    _base_style()
    plt.figure(figsize=(7.2, 5.6))
    plt.scatter(y_true, y_pred, alpha=0.45, s=18)
    line = np.linspace(min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max()), 100)
    plt.plot(line, line, "--", linewidth=1.6, color="#C44E52")
    plt.xlabel("True quality")
    plt.ylabel("Predicted quality")
    plt.title("Prediction vs Ground Truth")
    plt.tight_layout()
    plt.savefig(path, dpi=170)
    plt.close()


def save_quality_distribution_plot(path: Path, df: pd.DataFrame) -> None:
    _base_style()
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), gridspec_kw={"wspace": 0.28})

    bins = np.arange(df["quality"].min() - 0.5, df["quality"].max() + 1.5, 1)
    axes[0].hist(df["quality"], bins=bins, color="#4E79A7", edgecolor="white", alpha=0.95)
    axes[0].set_title("Quality Distribution")
    axes[0].set_xlabel("Quality")
    axes[0].set_ylabel("Count")

    red = df[df["wine_type"] == "red"]["quality"]
    white = df[df["wine_type"] == "white"]["quality"]
    axes[1].hist(white, bins=bins, alpha=0.75, label="white", color="#59A14F", edgecolor="white")
    axes[1].hist(red, bins=bins, alpha=0.75, label="red", color="#E15759", edgecolor="white")
    axes[1].set_title("Quality by Wine Type")
    axes[1].set_xlabel("Quality")
    axes[1].legend(frameon=False)

    fig.suptitle("Wine Quality Dataset Overview", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_model_comparison_plot(path: Path, reg_metrics: dict[str, dict[str, float]]) -> None:
    _base_style()
    metric_df = (
        pd.DataFrame(reg_metrics)
        .T.reset_index()
        .rename(columns={"index": "model"})
        .sort_values("r2", ascending=False)
    )

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), gridspec_kw={"wspace": 0.32})

    axes[0].bar(metric_df["model"], metric_df["r2"], color="#4E79A7")
    axes[0].set_title("R2 by Model")
    axes[0].set_ylabel("R2")
    axes[0].tick_params(axis="x", rotation=25)

    axes[1].bar(metric_df["model"], metric_df["rmse"], color="#F28E2B")
    axes[1].set_title("RMSE by Model")
    axes[1].set_ylabel("RMSE")
    axes[1].tick_params(axis="x", rotation=25)

    fig.suptitle("Regression Model Comparison", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_error_distribution_plot(path: Path, y_true: pd.Series, y_pred: np.ndarray) -> None:
    _base_style()
    errors = np.asarray(y_pred) - np.asarray(y_true)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), gridspec_kw={"wspace": 0.3})

    axes[0].hist(errors, bins=35, color="#76B7B2", edgecolor="white")
    axes[0].axvline(0, color="#C44E52", linestyle="--", linewidth=1.4)
    axes[0].set_title("Residual Distribution")
    axes[0].set_xlabel("Prediction Error (y_pred - y_true)")
    axes[0].set_ylabel("Count")

    abs_errors = np.abs(errors)
    axes[1].hist(abs_errors, bins=35, color="#B07AA1", edgecolor="white")
    axes[1].set_title("Absolute Error Distribution")
    axes[1].set_xlabel("Absolute Error")
    axes[1].set_ylabel("Count")

    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def save_feature_importance(
    path: Path,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    top_k: int = 12,
) -> pd.DataFrame:
    result = permutation_importance(model, X_test, y_test, n_repeats=8, random_state=42, n_jobs=2)
    feature_names = X_test.columns
    imp = pd.DataFrame({"feature": feature_names, "importance": result.importances_mean})
    top = imp.sort_values("importance", ascending=False).head(top_k)
    top.to_csv(path, index=False)
    return top


def save_feature_importance_plot(path: Path, importance_df: pd.DataFrame) -> None:
    _base_style()
    plot_df = importance_df.sort_values("importance", ascending=True)

    plt.figure(figsize=(7.6, 5.4))
    plt.barh(plot_df["feature"], plot_df["importance"], color="#4E79A7")
    plt.xlabel("Permutation Importance")
    plt.title("Top Feature Importance")
    plt.tight_layout()
    plt.savefig(path, dpi=170)
    plt.close()


def save_sommelier_notes(path: Path, X_test: pd.DataFrame, preds: np.ndarray) -> None:
    sample = X_test.copy()
    sample["pred_quality"] = np.round(preds, 2)
    sample = sample.sort_values("pred_quality", ascending=False).head(5)

    def note(row: pd.Series) -> str:
        tags = []
        if row["alcohol"] >= 12:
            tags.append("酒体偏强")
        if row["volatile acidity"] >= 0.45:
            tags.append("挥发酸偏高，个性明显")
        if row["residual sugar"] >= 7:
            tags.append("残糖较高，甜润")
        if row["citric acid"] >= 0.35:
            tags.append("柠檬酸贡献了清爽感")
        if row["sulphates"] >= 0.7:
            tags.append("硫酸盐特征更硬朗")
        if not tags:
            tags.append("结构均衡，风格克制")
        return "；".join(tags)

    lines = ["# Sommelier Bot Notes", ""]
    for i, (_, row) in enumerate(sample.iterrows(), start=1):
        lines.append(
            f"{i}. [{row['wine_type']}] 预测质量 {row['pred_quality']:.2f} -> {note(row)}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
