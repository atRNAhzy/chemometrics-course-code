# Week 05: Wine Quality 预测实验

本目录是第 5 周作业代码与结果入口。

作业内容说明（用于提交）：
- `作业说明.md`

## 快速开始

```bash
cd /mnt/shared/playground/AI-Chem-2026-37420232204783-黄子烨
pip install -r week05/requirements.txt
python week05/main.py

# AutoGluon 搜索（30分钟内，可选）
conda run -n aichem_week05 python week05/autogluon_search.py
```

如需在训练期间每 2 分钟推送进度（PushPlus）：

```bash
conda run -n aichem_week05 python week05/run_autogluon_with_push.py --token <your_token>
```

## 目录说明

- `main.py`：主实验入口（sklearn 训练与评估）
- `src/`：数据、建模、报告模块
- `autogluon_search.py`：AutoGluon 30 分钟搜索脚本（可选扩展）
- `run_autogluon_with_push.py`：训练过程进度推送脚本
- `results/`：运行后生成的结果

## 结果文件索引

- 指标汇总：`results/metrics_summary.json`
- 最优模型预测：`results/predictions_best_model.csv`
- 散点图：`results/prediction_scatter.png`
- 模型对比图：`results/model_comparison.png`
- 残差分布图：`results/error_distribution.png`
- 质量分布图：`results/quality_distribution_overview.png`
- 特征重要性：`results/feature_importance_top12.csv`、`results/feature_importance_top12.png`

备注：作业分析过程与结论见 `作业说明.md`。
