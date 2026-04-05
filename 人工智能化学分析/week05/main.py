from __future__ import annotations

from src.config import SETTINGS
from src.data import load_wine_dataset, prepare_raw_data
from src.modeling import (
    build_preprocessor,
    regression_metrics,
    split_data,
    train_regressors,
    train_tier_classifier,
)
from src.reporting import (
    save_error_distribution_plot,
    save_feature_importance,
    save_feature_importance_plot,
    save_metrics,
    save_model_comparison_plot,
    save_predictions,
    save_quality_distribution_plot,
    save_scatter_plot,
)



def main() -> None:
    prepare_raw_data(SETTINGS.red_csv, SETTINGS.white_csv)
    df = load_wine_dataset(SETTINGS.red_csv, SETTINGS.white_csv)

    X_train, X_test, y_train, y_test = split_data(
        df,
        test_size=SETTINGS.test_size,
        random_state=SETTINGS.random_state,
    )

    preprocessor = build_preprocessor(X_train.columns)
    models = train_regressors(preprocessor, random_state=SETTINGS.random_state)

    reg_metrics = {}
    best_name = ""
    best_score = float("inf")
    best_preds = None
    best_model = None

    print("=== Regression Training Start ===")
    total_models = len(models)
    for idx, (name, model) in enumerate(models.items(), start=1):
        print(f"[{idx}/{total_models}] training: {name}")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metrics = regression_metrics(y_test, preds)
        reg_metrics[name] = metrics
        print(
            f"    metrics -> MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}, R2={metrics['r2']:.4f}"
        )

        if metrics["rmse"] < best_score:
            best_name = name
            best_score = metrics["rmse"]
            best_preds = preds
            best_model = model
            print(f"    new best -> {best_name} (RMSE={best_score:.4f})")

    print("=== Classification Training Start (quality >= 7) ===")
    cls_metrics = train_tier_classifier(preprocessor, X_train, X_test, y_train, y_test)
    print(
        f"classification -> ACC={cls_metrics['accuracy']:.4f}, F1={cls_metrics['f1']:.4f}, ROC_AUC={cls_metrics['roc_auc']:.4f}"
    )

    results_dir = SETTINGS.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    save_metrics(
        results_dir / "metrics_summary.json",
        {
            "dataset": {"samples": int(len(df)), "features": int(df.shape[1] - 1)},
            "regression": reg_metrics,
            "best_model": best_name,
            "classification_quality>=7": cls_metrics,
        },
    )

    assert best_preds is not None and best_model is not None
    save_predictions(results_dir / "predictions_best_model.csv", y_test, best_preds)
    save_scatter_plot(results_dir / "prediction_scatter.png", y_test, best_preds)

    importance_df = save_feature_importance(
        results_dir / "feature_importance_top12.csv",
        best_model,
        X_test,
        y_test,
        top_k=12,
    )

    # Presentation-friendly figures.
    save_quality_distribution_plot(results_dir / "quality_distribution_overview.png", df)
    save_model_comparison_plot(results_dir / "model_comparison.png", reg_metrics)
    save_error_distribution_plot(results_dir / "error_distribution.png", y_test, best_preds)
    save_feature_importance_plot(results_dir / "feature_importance_top12.png", importance_df)

    best_r2 = reg_metrics[best_name]["r2"]
    print("=== Training Finished ===")
    print(f"Best model: {best_name} | RMSE={best_score:.4f} | R2={best_r2:.4f}")
    print(f"Results saved in: {results_dir}")


if __name__ == "__main__":
    main()
