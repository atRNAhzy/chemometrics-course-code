# Upgrade Playbook (Model-driven)

下表给出对低分样本的局部可操作调整建议，目标是提升模型预测质量（仅用于学习，不代表真实酿造工艺）。

| case | wine_type | pred_before | pred_after | gain | suggestions |
|---|---:|---:|---:|---:|---|
| 1 | red | 4.133 | 4.468 | 0.336 | chlorides -0.003; sulphates +0.020; sulphates +0.020; sulphates +0.020; sulphates +0.020; alcohol +0.150; sulphates +0.020 |
| 2 | red | 4.288 | 4.645 | 0.357 | sulphates +0.020; sulphates +0.020; sulphates +0.020; sulphates +0.020; sulphates +0.020; sulphates +0.020; citric acid +0.020 |
| 3 | red | 4.321 | 5.151 | 0.830 | alcohol +0.150; alcohol +0.150; alcohol +0.150; alcohol +0.150; sulphates +0.020; sulphates +0.020; sulphates +0.020 |
| 4 | white | 4.345 | 5.403 | 1.057 | alcohol +0.150; alcohol +0.150; alcohol +0.150; chlorides -0.003; volatile acidity -0.030; chlorides -0.003; chlorides -0.003 |
| 5 | red | 4.396 | 4.939 | 0.544 | sulphates +0.020; citric acid +0.020; chlorides -0.003; sulphates +0.020; sulphates +0.020; sulphates +0.020; sulphates +0.020 |
