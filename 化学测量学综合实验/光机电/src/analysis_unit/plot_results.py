"""
绘制滴定分析结果的可视化功能模块
包含拟合线绘制、交点标记、文本标签等功能
"""
import pyqtgraph as pg
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


class TitrationPlotter:
    """滴定分析结果绘制器"""
    
    def __init__(self, plot_widget):
        """
        初始化绘制器
        
        Args:
            plot_widget: pyqtgraph.PlotWidget 绘图控件
        """
        self.plot_widget = plot_widget
        self.fit_items = []  # 存储拟合相关的绘图项目
    
    def clear_fit_items(self):
        """清除所有拟合相关的绘图项目"""
        for item in self.fit_items:
            self.plot_widget.removeItem(item)
        self.fit_items = []
    
    def _refit_in_time_domain(self, data_y, time_list, prop_list, intersection_x):
        """
        在时间坐标系下重新拟合左右两段直线
        
        Args:
            data_y: 原始 y 数据
            time_list: 时间列表  
            prop_list: proportion 列表
            intersection_x: 交点的 proportion 坐标
            
        Returns:
            dict: 包含左右段时间域拟合结果的字典
        """
        if not time_list or not prop_list or not data_y:
            return None
            
        if len(time_list) != len(prop_list) or len(time_list) != len(data_y):
            return None
            
        # 将数据转换为 numpy 数组
        times = np.array(time_list)
        props = np.array(prop_list) 
        ys = np.array(data_y)
        
        # 根据交点分割数据
        left_mask = props <= intersection_x
        right_mask = props >= intersection_x
        
        # 左段数据
        left_times = times[left_mask]
        left_ys = ys[left_mask]
        
        # 右段数据  
        right_times = times[right_mask]
        right_ys = ys[right_mask]
        
        result = {}
        
        # 拟合左段 (时间域)
        if len(left_times) >= 2:
            left_model = LinearRegression()
            left_X = left_times.reshape(-1, 1)
            left_model.fit(left_X, left_ys)
            left_pred = left_model.predict(left_X)
            left_r2 = r2_score(left_ys, left_pred)
            
            result['left'] = {
                'slope': float(left_model.coef_[0]),
                'intercept': float(left_model.intercept_),
                'r2': float(left_r2),
                'time_range': [float(left_times.min()), float(left_times.max())]
            }
        
        # 拟合右段 (时间域)
        if len(right_times) >= 2:
            right_model = LinearRegression()
            right_X = right_times.reshape(-1, 1)
            right_model.fit(right_X, right_ys)
            right_pred = right_model.predict(right_X)
            right_r2 = r2_score(right_ys, right_pred)
            
            result['right'] = {
                'slope': float(right_model.coef_[0]),
                'intercept': float(right_model.intercept_), 
                'r2': float(right_r2),
                'time_range': [float(right_times.min()), float(right_times.max())]
            }
            
        return result
    
    def plot_analysis_results(self, result_dict, data_y=None, time_list=None, prop_list=None):
        """
        绘制完整的分析结果，包括拟合线、交点和标签
        
        Args:
            result_dict: 分析结果字典，包含拟合参数和交点信息
            data_y: 原始数据的y值列表，用于计算标签位置
            time_list: 时间列表，用于时间域拟合
            prop_list: proportion 列表，用于时间域拟合
        """
        # 清除之前的拟合项目
        self.clear_fit_items()
        
        # 提取关键数据
        intersection_x = result_dict.get('V_eq')
        intersection_y = result_dict.get('Y_eq')

        # 如果提供了时间和proportion数据，在时间域重新拟合
        if time_list and prop_list and data_y:
            time_fit_result = self._refit_in_time_domain(data_y, time_list, prop_list, intersection_x)
            if time_fit_result:
                # 使用时间域拟合结果绘制
                self._plot_time_domain_fit_lines(time_fit_result, data_y, time_list, prop_list)
            else:
                # 回退到原来的方法
                self._plot_fit_lines(result_dict, intersection_x, data_y, time_list, prop_list)
        else:
            # 使用原来的方法（proportion 域）
            self._plot_fit_lines(result_dict, intersection_x, data_y, time_list, prop_list)

        # 绘制交点（横坐标需要转换为时间，如果提供映射）
        self._plot_intersection_point(intersection_x, intersection_y, data_y, time_list, prop_list)
        
        # 在左上角显示统一的信息框
        self._plot_analysis_info_box(result_dict, time_fit_result if time_list and prop_list and data_y else None, data_y, time_list, prop_list)
        
    def _plot_time_domain_fit_lines(self, time_fit_result, data_y, time_list, prop_list):
        """绘制时间域拟合的直线"""
        
        # 绘制左段时间域拟合线
        if 'left' in time_fit_result:
            left_fit = time_fit_result['left']
            self._plot_time_domain_segment(
                left_fit, 'left', data_y, time_list, prop_list, 
                color=(220, 20, 60), label_pos_factor=0.9
            )
        
        # 绘制右段时间域拟合线
        if 'right' in time_fit_result:
            right_fit = time_fit_result['right']
            self._plot_time_domain_segment(
                right_fit, 'right', data_y, time_list, prop_list,
                color=(220, 20, 60), label_pos_factor=0.8
            )
    
    def _plot_time_domain_segment(self, fit_params, segment_name, data_y, time_list, prop_list, color, label_pos_factor):
        """绘制单个时间域拟合线段"""
        slope = fit_params['slope']
        intercept = fit_params['intercept']
        r2 = fit_params['r2']
        time_range = fit_params['time_range']
        
        # 在时间范围内绘制直线
        t_start, t_end = time_range
        # 稍微扩展范围以便更好显示
        t_margin = (t_end - t_start) * 0.1
        t_plot_start = max(min(time_list), t_start - t_margin)
        t_plot_end = min(max(time_list), t_end + t_margin)
        
        # 生成直线点
        t_line = np.linspace(t_plot_start, t_plot_end, 100)
        y_line = slope * t_line + intercept
        
        # 绘制直线
        pen = pg.mkPen(color=color, width=4)
        line_curve = self.plot_widget.plot(t_line, y_line, pen=pen)
        self.fit_items.append(line_curve)
    
    def _plot_fit_lines(self, result_dict, intersection_x, data_y, time_list=None, prop_list=None):
        """绘制左右两段拟合线及其标签"""
        # 左段拟合线
        slope_left = result_dict.get('slope_left')
        intercept_left = result_dict.get('intercept_left')
        r2_left = result_dict.get('r2_left')
        
        if slope_left is not None and intercept_left is not None:
            self._plot_left_segment(slope_left, intercept_left, r2_left,
                                  intersection_x, data_y, time_list, prop_list)
        
        # 右段拟合线
        slope_right = result_dict.get('slope_right')
        intercept_right = result_dict.get('intercept_right')
        r2_right = result_dict.get('r2_right')
        
        if slope_right is not None and intercept_right is not None:
            self._plot_right_segment(slope_right, intercept_right, r2_right,
                                   intersection_x, data_y, time_list, prop_list)
    
    def _plot_left_segment(self, slope, intercept, r2, intersection_x, data_y, time_list=None, prop_list=None):
        """绘制左段拟合线及标签"""
        # x范围限制在0到交点，但不超过1
        x_prop_left = [0.0, min(intersection_x, 1.0)]

        # 预先准备 xp/fp 插值数组（如果提供）以便后续标签定位使用
        xp = None
        fp = None
        if time_list is not None and prop_list is not None and len(time_list) and len(prop_list):
            pairs = sorted(zip(time_list, prop_list), key=lambda p: p[0])
            xp = [p[0] for p in pairs]
            fp = [p[1] for p in pairs]

        # 如果提供 time/proportion 映射，则在时间轴上绘制拟合曲线：
        # y(t) = slope * prop(t) + intercept
        if xp is not None and fp is not None:
            def prop_of_t(t):
                if not xp:
                    return 0.0
                if t <= xp[0]:
                    return fp[0]
                if t >= xp[-1]:
                    return fp[-1]
                for i in range(len(xp)-1):
                    if xp[i] <= t <= xp[i+1]:
                        x0, x1 = xp[i], xp[i+1]
                        y0, y1 = fp[i], fp[i+1]
                        if x1 == x0:
                            return y0
                        tt = (t - x0) / (x1 - x0)
                        return y0 + tt * (y1 - y0)
                return fp[-1]

            # 为稳健，直接在整个时间范围内采样若干点并筛选出满足 prop in x_prop_left
            t_min, t_max = xp[0], xp[-1]
            sample_n = min(300, max(50, len(xp)))
            ts = [t_min + (t_max - t_min) * i / (sample_n - 1) for i in range(sample_n)]
            tx = []
            ty = []
            for t in ts:
                p = prop_of_t(t)
                if x_prop_left[0] - 1e-12 <= p <= x_prop_left[1] + 1e-12:
                    tx.append(t)
                    ty.append(slope * p + intercept)

            pen_left = pg.mkPen(color=(220, 20, 60), width=4)
            left_curve = None
            if tx and ty:
                left_curve = self.plot_widget.plot(tx, ty, pen=pen_left)
        else:
            # 回退：在比例轴上绘制（兼容旧逻辑）
            x_left = x_prop_left
            y_left = [slope * x + intercept for x in x_left]
            pen_left = pg.mkPen(color=(220, 20, 60), width=4)
            left_curve = self.plot_widget.plot(x_left, y_left, pen=pen_left)

        if left_curve is not None:
            self.fit_items.append(left_curve)


    
    def _plot_right_segment(self, slope, intercept, r2, intersection_x, data_y, time_list=None, prop_list=None):
        """绘制右段拟合线及标签"""
        # x范围限制在交点到1.0
        x_prop_right = [max(intersection_x, 0.0), 1.0]

        if time_list is not None and prop_list is not None and len(time_list) and len(prop_list):
            pairs = sorted(zip(time_list, prop_list), key=lambda p: p[0])
            xp = [p[0] for p in pairs]
            fp = [p[1] for p in pairs]

            def prop_of_t(t):
                if not xp:
                    return 0.0
                if t <= xp[0]:
                    return fp[0]
                if t >= xp[-1]:
                    return fp[-1]
                for i in range(len(xp)-1):
                    if xp[i] <= t <= xp[i+1]:
                        x0, x1 = xp[i], xp[i+1]
                        y0, y1 = fp[i], fp[i+1]
                        if x1 == x0:
                            return y0
                        tt = (t - x0) / (x1 - x0)
                        return y0 + tt * (y1 - y0)
                return fp[-1]

            t_min, t_max = xp[0], xp[-1]
            sample_n = min(300, max(50, len(xp)))
            ts = [t_min + (t_max - t_min) * i / (sample_n - 1) for i in range(sample_n)]
            tx = []
            ty = []
            for t in ts:
                p = prop_of_t(t)
                if x_prop_right[0] - 1e-12 <= p <= x_prop_right[1] + 1e-12:
                    tx.append(t)
                    ty.append(slope * p + intercept)

            pen_right = pg.mkPen(color=(220, 20, 60), width=4)
            right_curve = None
            if tx and ty:
                right_curve = self.plot_widget.plot(tx, ty, pen=pen_right)
        else:
            x_right = x_prop_right
            y_right = [slope * x + intercept for x in x_right]
            pen_right = pg.mkPen(color=(220, 20, 60), width=4)
            right_curve = self.plot_widget.plot(x_right, y_right, pen=pen_right)
        self.fit_items.append(right_curve)
        

    
    def _plot_intersection_point(self, intersection_x, intersection_y, data_y, time_list=None, prop_list=None):
        """绘制交点标记及标签"""
        if intersection_x is None or intersection_y is None:
            return
        
        # 交点圆圈标记
        # 如果提供 time/proportion 映射，则将交点的 proportion x 转换为时间再绘制
        if time_list is not None and prop_list is not None and len(time_list) and len(prop_list):
            pairs = sorted(zip(time_list, prop_list), key=lambda p: p[0])
            xp = [p[0] for p in pairs]
            fp = [p[1] for p in pairs]

            # 找到与 intersection_x 最接近的时间（通过查找 p closest to intersection_x）
            t_at_x = None
            best_diff = None
            for t, p in zip(xp, fp):
                d = abs(p - intersection_x)
                if best_diff is None or d < best_diff:
                    best_diff = d
                    t_at_x = t
            draw_x = t_at_x if t_at_x is not None else intersection_x
        else:
            draw_x = intersection_x

        point_plot = self.plot_widget.plot(
            [draw_x], [intersection_y], 
            pen=None, symbol='o', 
            symbolBrush=(220, 20, 60), 
            symbolPen=(220, 20, 60),
            symbolSize=12
        )
        self.fit_items.append(point_plot)
        
        # 交点标签
        label_text = f"交点: ({intersection_x:.3f}, {intersection_y:.1f})"
        text_item = pg.TextItem(
            html=f"<span style='color:#dc143c; font-size:11pt; font-weight:bold; background-color:rgba(255,255,255,200)'>{label_text}</span>"
        )
        
        # 计算标签位置（中下方空白处）
        if data_y:
            y_range_min = min(data_y)
            y_offset = y_range_min + (max(data_y) - y_range_min) * 0.2
            text_item.setPos(intersection_x, y_offset)
        else:
            text_item.setPos(intersection_x, 50)
        
        text_item.setAnchor((0.5, 0))  # 居中对齐
        self.plot_widget.addItem(text_item)
        self.fit_items.append(text_item)
    
    def _plot_analysis_info_box(self, result_dict, time_fit_result, data_y, time_list=None, prop_list=None):
        """在图片左上角显示统一的分析信息框"""
        # 获取NaOH浓度
        naoh_conc = result_dict.get('NaOH_conc')
        if naoh_conc is None:
            return
        
        # 构建信息文本
        info_lines = []
        
        # 第一行：NaOH浓度
        info_lines.append(f"c(NaOH) = {naoh_conc:.4f} mol/L")
        
        # 获取拟合信息
        if time_fit_result:
            # 使用时间域拟合结果
            if 'left' in time_fit_result:
                left_fit = time_fit_result['left']
                info_lines.append(f"左段: y = {left_fit['slope']:.3f}t + {left_fit['intercept']:.3f}, R² = {left_fit['r2']:.4f}")
            
            if 'right' in time_fit_result:
                right_fit = time_fit_result['right']  
                info_lines.append(f"右段: y = {right_fit['slope']:.3f}t + {right_fit['intercept']:.3f}, R² = {right_fit['r2']:.4f}")
        else:
            # 使用原始proportion域拟合结果
            slope_left = result_dict.get('slope_left')
            intercept_left = result_dict.get('intercept_left')
            r2_left = result_dict.get('r2_left')
            
            slope_right = result_dict.get('slope_right')
            intercept_right = result_dict.get('intercept_right')
            r2_right = result_dict.get('r2_right')
            
            if all(v is not None for v in [slope_left, intercept_left, r2_left]):
                info_lines.append(f"左段: y = {slope_left:.3f}x + {intercept_left:.3f}, R² = {r2_left:.4f}")
            
            if all(v is not None for v in [slope_right, intercept_right, r2_right]):
                info_lines.append(f"右段: y = {slope_right:.3f}x + {intercept_right:.3f}, R² = {r2_right:.4f}")
        
        # 创建信息框
        info_text = "<br>".join(info_lines)
        text_item = pg.TextItem(
            html=f"""<div style='color:#dc143c; font-size:11pt; font-weight:bold; 
                      background-color:rgba(255,255,255,240); padding:10px; 
                      border:2px solid #dc143c; border-radius:5px;'>{info_text}</div>"""
        )
        
        # 计算左上角位置
        if data_y and time_list:
            x_min = min(time_list) if time_list else 0.0
            y_max = max(data_y)
            # 稍微向内偏移
            label_x = x_min + (max(time_list) - x_min) * 0.02 if time_list else 0.02
            label_y = y_max * 0.98
        elif data_y:
            # 如果没有时间数据，使用默认比例坐标
            label_x = 0.02
            label_y = max(data_y) * 0.98
        else:
            # 完全默认位置
            label_x = 0.02
            label_y = 380
            
        text_item.setPos(label_x, label_y)
        text_item.setAnchor((0, 1))  # 左上角对齐
        self.plot_widget.addItem(text_item)
        self.fit_items.append(text_item)
    
    def get_analysis_summary_text(self, result_dict):
        """
        生成分析结果摘要文本
        
        Args:
            result_dict: 分析结果字典
            
        Returns:
            str: 格式化的分析结果文本
        """
        lines = []
        
        # 基本信息
        intersection_x = result_dict.get('V_eq')
        intersection_y = result_dict.get('Y_eq') 
        c_naoh = result_dict.get('NaOH_conc')
        
        if intersection_x is not None and c_naoh is not None:
            lines.append(f"分析完成：交点 x={intersection_x:.4f}, c(NaOH)={c_naoh:.4f} mol/L")
        
        # 拟合参数
        slope_left = result_dict.get('slope_left')
        intercept_left = result_dict.get('intercept_left')
        r2_left = result_dict.get('r2_left')
        
        slope_right = result_dict.get('slope_right')
        intercept_right = result_dict.get('intercept_right')
        r2_right = result_dict.get('r2_right')
        
        if all(v is not None for v in [slope_left, intercept_left, r2_left]):
            lines.append(f"左段拟合: y = {slope_left:.3f}x + {intercept_left:.3f}, R² = {r2_left:.4f}")
        
        if all(v is not None for v in [slope_right, intercept_right, r2_right]):
            lines.append(f"右段拟合: y = {slope_right:.3f}x + {intercept_right:.3f}, R² = {r2_right:.4f}")
        
        # 拟合方法
        ratio_method = result_dict.get('ratio_method')
        if ratio_method:
            lines.append(f"拟合方法: {ratio_method}")
        
        return '\n'.join(lines)


def create_titration_plotter(plot_widget):
    """
    工厂函数：创建滴定绘图器实例
    
    Args:
        plot_widget: pyqtgraph.PlotWidget 绘图控件
        
    Returns:
        TitrationPlotter: 绘图器实例
    """
    return TitrationPlotter(plot_widget)