import numpy as np
from scipy import stats
import matplotlib.pyplot as plt



def linear_fit_analysis(data, r2_threshold=0.8, filename='linear_fit.png'):
    """
    二维数据线性拟合分析工具
    
    参数：
    data : np.ndarray - 二维数组，形状为(N, 2)，包含x,y数据点
    r2_threshold : float - 判定线性关系的R²阈值，默认0.8
    filename : str - 输出图像文件名，默认'linear_fit.png'
    
    返回：
    tuple: (斜率, 截距, R²值, 是否具有线性关系)
    """
    # 数据解构与校验
    x = data[:, 0]
    y = data[:, 1]
    
    # 执行线性回归
    slope, intercept, r_value, _, _ = stats.linregress(x, y)
    r_squared = r_value**2
    
    # 判断线性关系
    has_linear = r_squared >= r2_threshold
    
    # 创建专业可视化
    plt.figure(figsize=(10, 6), dpi=300)
    
    # 散点图（原始数据）
    plt.scatter(x, y, 
                c='#1f77b4',     # 标准蓝色
                edgecolor='k',  # 黑色边框
                alpha=0.7, 
                label='Data Points',
                zorder=3)
    
    # 拟合直线
    fit_line = slope * x + intercept
    plt.plot(x, fit_line, 
             color='#d62728',  # 标准红色
             lw=2, 
             label=f'Fitted Line: $y = {slope:.2f}x + {intercept:.2f}$',
             zorder=2)
    
    # 残差连线（增强可视化效果）
    plt.vlines(x, y, fit_line, 
               colors='gray', 
               linestyles='dashed',
               alpha=0.4,
               zorder=1)
    
    # 样式配置
    plt.title(f'Linear Regression Analysis (R² = {r_squared:.3f})', fontsize=14, pad=20)
    plt.xlabel('X', fontsize=12, labelpad=10)
    plt.ylabel('Y', fontsize=12, labelpad=10)
    plt.grid(True, 
            linestyle='--', 
            alpha=0.6,
            zorder=0)
    plt.legend(frameon=True, 
              framealpha=0.9, 
              loc='best')
    
    

    # 保存高清图像
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.show()
    plt.close()
    
    return slope, intercept, r_squared, has_linear

# 测试用例
if __name__ == "__main__":
    # 生成测试数据

    data = np.array([[0, 0.0284],[1,0.2672],[2,0.5406],[3 ,0.8201],[4,1.1089],[5,1.3918]])
    # 执行分析
    slope, intercept, r2, is_linear = linear_fit_analysis(data)
    
    print(f"斜率: {slope:.4f}")
    print(f"截距: {intercept:.4f}")
    print(f"R²值: {r2:.4f}")
    print(f"线性关系: {'是' if is_linear else '否'}")