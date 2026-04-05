from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline



def save_style_clusters(path: Path, df: pd.DataFrame, random_state: int, n_clusters: int = 4) -> None:
    chem_cols = [c for c in df.columns if c not in {"quality", "wine_type"}]
    profile_data = df[chem_cols + ["quality"]].copy()

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    labels = model.fit_predict(profile_data[chem_cols])
    profile_data["cluster"] = labels
    profile_data["wine_type"] = df["wine_type"].values

    summary = (
        profile_data.groupby("cluster", as_index=False)
        .agg(
            samples=("quality", "size"),
            avg_quality=("quality", "mean"),
            avg_alcohol=("alcohol", "mean"),
            avg_acidity=("volatile acidity", "mean"),
            avg_sugar=("residual sugar", "mean"),
            white_ratio=("wine_type", lambda s: float((s == "white").mean())),
        )
        .sort_values("avg_quality", ascending=False)
    )
    summary = summary.round(3)
    summary.to_csv(path, index=False)



def save_upgrade_playbook(
    path: Path,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    top_n: int = 5,
    max_steps: int = 7,
) -> None:
    target_rows = X_test.copy()
    target_rows["y_true"] = y_test.values
    target_rows["y_pred"] = model.predict(X_test)
    target_rows = target_rows.sort_values(["y_pred", "y_true"]).head(top_n)

    bounds_min = X_test.min(numeric_only=True)
    bounds_max = X_test.max(numeric_only=True)

    rules = {
        "alcohol": +0.15,
        "volatile acidity": -0.03,
        "citric acid": +0.02,
        "sulphates": +0.02,
        "chlorides": -0.003,
    }

    lines = [
        "# Upgrade Playbook (Model-driven)",
        "",
        "下表给出对低分样本的局部可操作调整建议，目标是提升模型预测质量（仅用于学习，不代表真实酿造工艺）。",
        "",
        "| case | wine_type | pred_before | pred_after | gain | suggestions |",
        "|---|---:|---:|---:|---:|---|",
    ]

    for i, (_, row) in enumerate(target_rows.iterrows(), start=1):
        cur = row.drop(labels=["y_true", "y_pred"]).copy()
        base_pred = float(model.predict(pd.DataFrame([cur]))[0])

        suggestions: list[str] = []
        for _ in range(max_steps):
            best_feature = None
            best_candidate = base_pred

            for feat, step in rules.items():
                candidate = cur.copy()
                candidate[feat] = float(np.clip(candidate[feat] + step, bounds_min[feat], bounds_max[feat]))
                pred = float(model.predict(pd.DataFrame([candidate]))[0])
                if pred > best_candidate + 1e-6:
                    best_candidate = pred
                    best_feature = feat

            if best_feature is None:
                break

            cur[best_feature] = float(
                np.clip(cur[best_feature] + rules[best_feature], bounds_min[best_feature], bounds_max[best_feature])
            )
            base_pred = best_candidate
            sign = "+" if rules[best_feature] > 0 else ""
            suggestions.append(f"{best_feature} {sign}{rules[best_feature]:.3f}")

        final_pred = float(model.predict(pd.DataFrame([cur]))[0])
        gain = final_pred - float(row["y_pred"])

        lines.append(
            f"| {i} | {row['wine_type']} | {row['y_pred']:.3f} | {final_pred:.3f} | {gain:.3f} | {'; '.join(suggestions) if suggestions else 'no-op'} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
