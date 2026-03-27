import numpy as np
import os
import time
from typing import Sequence, Optional, Dict
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# 默认保存目录
DEFAULT_SAVE_DIR = r"../results"

def _format_number(value: Optional[float], precision: int = 4) -> Optional[float]:
    """格式化数字到指定精度"""
    return None if value is None else round(float(value), precision)

def _resolve_save_path(save_txt_path: Optional[str], filename: Optional[str]) -> str:
    """解析保存路径"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base_filename = f"titration_analysis_{timestamp}.txt"
    
    if filename:
        base_filename = filename if filename.endswith('.txt') else f"{filename}.txt"
    
    if save_txt_path is None:
        os.makedirs(DEFAULT_SAVE_DIR, exist_ok=True)
        return os.path.join(DEFAULT_SAVE_DIR, base_filename)
    
    if os.path.isdir(save_txt_path):
        return os.path.join(save_txt_path, base_filename)
    
    return save_txt_path

def _fit_linear_segment(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """使用sklearn进行线性拟合"""
    if len(x) < 2:
        raise ValueError("线性拟合至少需要2个点")
    
    # 使用sklearn的线性回归
    model = LinearRegression()
    X = x.reshape(-1, 1)
    model.fit(X, y)
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    return {
        'slope': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'r2': float(r2)
    }

def _find_global_minimum(x: np.ndarray, y: np.ndarray) -> int:
    """找到全局最小值的索引位置"""
    min_idx = np.argmin(y)
    # 确保分割点不在边界（至少留3个点用于拟合）
    min_idx = max(3, min(min_idx, len(x) - 4))

    return min_idx

def analyze_titration_from_curve(
    *,
    x: Sequence[float],
    y: Sequence[float], 
    hcl_conc: float,
    save_txt_path: Optional[str] = None,
    ratio_method: str = "mean",
    filename: Optional[str] = None,
) -> Dict[str, Optional[float]]:
    """
    滴定曲线分析主函数：
    1) 找到全局最小值作为分割点
    2) 最小值左边数据拟合直线1
    3) 最小值右边数据拟合直线2
    4) 计算两条直线交点 
    5) 根据 HCL:NaOH=c(NaOH):c(HCL) 计算浓度
    """
    # ---------- 数据准备 ----------
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.shape != y.shape:
        raise ValueError("x 和 y 的长度必须一致")
    if len(x) < 8:
        raise ValueError("数据点太少，至少需要 8 个点")

    # 按x排序，确保数据有序
    sort_indices = np.argsort(x)
    x_clean = x[sort_indices]
    y_clean = y[sort_indices]

    # ---------- 找到全局最小值作为分割点 ----------
    split_idx = _find_global_minimum(x_clean, y_clean)

    # ---------- 两段线性拟合 ----------
    x_left, y_left = x_clean[:split_idx], y_clean[:split_idx]
    x_right, y_right = x_clean[split_idx:], y_clean[split_idx:]

    try:
        fit_left = _fit_linear_segment(x_left, y_left)
        fit_right = _fit_linear_segment(x_right, y_right)
    except Exception as e:
        raise ValueError(f"线性拟合失败: {e}")

    # ---------- 计算交点 ----------
    slope_diff = fit_left['slope'] - fit_right['slope']
    if abs(slope_diff) < 1e-12:
        raise ArithmeticError("两段直线平行，无法计算交点")
    
    x_intersection = (fit_right['intercept'] - fit_left['intercept']) / slope_diff
    y_intersection = fit_left['slope'] * x_intersection + fit_left['intercept']

    # ---------- 计算NaOH浓度 ----------
    # 交点横坐标即为HCL占比，根据 HCL:NaOH = c(NaOH):c(HCL)
    # 即 x_intersection : (1-x_intersection) = naoh_conc : hcl_conc
    # 所以 naoh_conc = hcl_conc * x_intersection / (1-x_intersection)
    
    if abs(x_intersection - 1.0) < 1e-12:
        raise ArithmeticError("交点位于边界，无法计算浓度")
    
    naoh_conc = hcl_conc * x_intersection / (1 - x_intersection)

    # ---------- 构建结果字典 ----------
    result_dict = {
        "slope_left": _format_number(fit_left['slope']),
        "intercept_left": _format_number(fit_left['intercept']),  
        "r2_left": _format_number(fit_left['r2']),
        "slope_right": _format_number(fit_right['slope']),
        "intercept_right": _format_number(fit_right['intercept']),
        "r2_right": _format_number(fit_right['r2']),
        "V_eq": _format_number(x_intersection),
        "Y_eq": _format_number(y_intersection),
        "ratio_method": "intersection_based",
        "ratio_value": _format_number(x_intersection / (1 - x_intersection)),
        "HCl_conc": _format_number(hcl_conc),
        "NaOH_conc": _format_number(naoh_conc),
    }

    # ---------- 保存结果到文件 ----------
    try:
        save_path = _resolve_save_path(save_txt_path, filename)
        
        with open(save_path, "w", encoding="utf-8-sig") as f:
            f.write(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            f.write(f"\n==== 分析结果 ====\n")
            f.write(f"全局最小值位置: {x_clean[split_idx]:.6f}\n")
            f.write(f"左段拟合: y = {fit_left['slope']:.4f}x + {fit_left['intercept']:.4f} (R² = {fit_left['r2']:.4f})\n")
            f.write(f"右段拟合: y = {fit_right['slope']:.4f}x + {fit_right['intercept']:.4f} (R² = {fit_right['r2']:.4f})\n")
            f.write(f"交点: ({x_intersection:.6f}, {y_intersection:.6f})\n")
            f.write(f"HCl浓度: {hcl_conc:.6f} mol/L\n")
            f.write(f"NaOH浓度: {naoh_conc:.6f} mol/L\n")
            
            f.write("==== 原始数据 ====\n")
            f.write("x_fraction\ty_conductance\n")
            for xi, yi in zip(x, y):
                f.write(f"{xi:.6f}\t{yi:.6f}\n")
            

        
        result_dict["_saved_txt_path"] = save_path
        
    except Exception as e:
        print(f"保存文件失败: {e}")
    
    return result_dict
