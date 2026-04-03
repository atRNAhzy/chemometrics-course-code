# Week 03: pKa 预测实验

本目录对应《化学自动化》课程第 3 次作业，主题是用机器学习预测有机酸分子的 `pKa`。

## 保留文件

- `pKa_prediction_experiment.ipynb`
  作业主文件，包含数据读取、可视化、特征构建、模型比较、随机森林调参、特征重要性分析、逐步特征选择和 AutoGluon 补充部分。
- `data/Opt1_acidic_tr_CMF.csv`
  训练集，共 2220 个分子。
- `data/Opt1_acidic_tst_CMF.csv`
  测试集，共 740 个分子。
- `results/`
  Notebook 运行后输出的结果目录，用于保存 JSON 汇总、模型比较表和 AutoGluon 结果。
- `操作说明.md`
  教师提供的原始实验要求。
- `requirements.txt`
  运行 Notebook 推荐安装的依赖。

## 使用方式

在仓库根目录执行：

```bash
cd /mnt/shared/playground/AI-Chem-2026-37420232204783-黄子烨
conda activate aichem_week03
pip install -r week03/requirements.txt
jupyter notebook
```

然后打开：

`week03/pKa_prediction_experiment.ipynb`

按顺序运行全部单元格即可。

Notebook 默认会：

- 从 `week03/data/` 读取训练集和测试集
- 把结果文件写到 `week03/results/`

## Notebook 内容

- 数据集规模统计
- pKa 分布和分子量分布直方图
- Morgan Fingerprint、MACCSKeys、RDKit 描述符构建
- sklearn 多模型快速比较
- 随机森林交叉验证调参
- MACCSKeys 重要特征分析
- RDKit 描述符重要性分析
- RDKit 描述符逐步特征选择
- 新分子 pKa 预测
- AutoGluon 自动调参与结果比较
