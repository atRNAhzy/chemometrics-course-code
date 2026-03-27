"""
分析单元模块：包含数据分析、模拟数据生成等功能
"""

import random
import time
import math


class TitrationSimulator:
    """滴定模拟器：生成两段直线 + 高斯噪声的电导数据"""
    
    def __init__(self, max_speed: int, inc_ms: int, total_points: int = 10000, 
                 noise_std: float = 0.5):
        """
        初始化滴定模拟器
        
        Args:
            max_speed: 最大电机速度
            inc_ms: 递增间隔时间（毫秒）
            total_points: 总数据点数
            noise_std: 高斯噪声标准差（降低噪声强度）
        """
        self.max_speed = abs(max_speed)
        self.inc_ms = max(1, inc_ms)
        self.total_points = total_points
        self.noise_std = noise_std
        self.current_point = 0
        self.sp1 = 0
        self.sp2 = self.max_speed
        self.last_time = time.time()
        self.titrating = True
        
        # 随机生成两段直线参数（适配归一化坐标0-1）
        self.r_eq = random.uniform(0.3, 0.7)     # 交点在0-1范围内
        self.a1 = random.uniform(-200.0, -50.0)  # 左段斜率（负值）
        self.a2 = random.uniform(50.0, 200.0)    # 右段斜率（正值）
        self.b1 = random.uniform(150.0, 300.0)   # 左段截距
        self.b2 = (self.a1 - self.a2) * self.r_eq + self.b1  # 右段截距，确保交点一致
    def _get_conductivity(self, normalized_speed: float) -> float:
        """根据归一化电机速度 (sp1/max_speed) 计算电导值"""
        if normalized_speed <= self.r_eq:
            y = self.a1 * normalized_speed + self.b1
        else:
            y = self.a2 * normalized_speed + self.b2
        # 添加较小的高斯噪声
        y += random.gauss(0.0, self.noise_std)
        # 限制在 [0, 400] 范围内
        return y
    
    def get_next_data(self):
        """获取下一个数据点，返回 (sp1, sp2, cond) 或 None（如果结束）"""
        if not self.titrating or self.current_point >= self.total_points:
            return None
            
        current_time = time.time()
        if (current_time - self.last_time) * 1000 < self.inc_ms:
            return None  # 还没到下一个采样时间
            
        self.last_time = current_time
        
        # 推进速度（模仿 Arduino 逻辑）
        if self.sp1 < self.max_speed:
            self.sp1 += 1
        if self.sp2 > 0:
            self.sp2 -= 1
            
        # 计算电导值 - 基于归一化的电机1速度（与绘图坐标一致）
        normalized_speed = float(self.sp1) / self.max_speed if self.max_speed > 0 else 0.0
        cond = self._get_conductivity(normalized_speed)
        
        self.current_point += 1
        
        # 检查是否结束
        if self.current_point >= self.total_points or (self.sp1 >= self.max_speed and self.sp2 <= 0):
            self.titrating = False
            
        return (self.sp1, self.sp2, cond)
    
    def is_finished(self) -> bool:
        """检查是否完成滴定"""
        return not self.titrating or self.current_point >= self.total_points
    
    def reset(self):
        """重置模拟器状态"""
        self.current_point = 0
        self.sp1 = 0
        self.sp2 = self.max_speed
        self.last_time = time.time()
        self.titrating = True
        
        # 重新生成随机参数（适配归一化坐标0-1）
        self.r_eq = random.uniform(0.3, 0.7)     # 交点在0-1范围内
        self.a1 = random.uniform(-200.0, -50.0)  # 左段斜率（负值）
        self.a2 = random.uniform(50.0, 200.0)    # 右段斜率（正值）
        self.b1 = random.uniform(150.0, 300.0)   # 左段截距
        self.b2 = (self.a1 - self.a2) * self.r_eq + self.b1
    
    def get_curve_parameters(self) -> dict:
        """获取当前曲线参数信息"""
        return {
            'intersection_r': self.r_eq,
            'left_slope': self.a1,
            'right_slope': self.a2,
            'left_intercept': self.b1,
            'right_intercept': self.b2,
            'noise_std': self.noise_std
        }