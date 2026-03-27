import os
import time
from dataclasses import dataclass
from typing import Optional

from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg

from ui import MainForm
from analysis_unit import (
    analyze_titration_from_curve, 
    TitrationSimulator, 
    create_titration_plotter
)
from serial_unit import SerialController


@dataclass
class AppConfig:
    """应用配置常量"""
    # 绘图配置
    PLOT_SYMBOL_SIZE: int = 5
    PLOT_COLOR_RGB: tuple = (0, 114, 178)
    X_AXIS_RANGE: tuple = (0, 1.0)
    X_AXIS_LIMIT_ENABLED: bool = False
    DEFAULT_Y_RANGE: tuple = (0, 400)
    Y_AXIS_MARGIN_RATIO: float = 0.1
    
    # 定时器配置
    SIMULATION_INTERVAL_MS: int = 50
    
    # 文件配置
    DEFAULT_RESULTS_FOLDER: str = "results"
    FILE_EXTENSION: str = ".txt"
    FILENAME_TIME_FORMAT: str = "%Y%m%d_%H%M%S"


class AppController(QtCore.QObject):
    #region ---------- 初始化 ----------
    def __init__(self, ui, parent=None):
        super().__init__(parent)
        self.ui = ui

        # 初始化串口和数据组件
        self._init_serial_controller()
        self._data_generator = None
        
        # 初始化组件
        self._init_components()
        self._setup_ui_connections()
        self._init_timer()
        
        self._refresh_ports()
        self._plot_paused = False

    def _init_serial_controller(self):
        """初始化串口控制器"""
        self.serial_controller = None
        if SerialController:
            self.serial_controller = SerialController(self)
            self.serial_controller.data_received.connect(self._on_serial_data)
            self.serial_controller.connection_changed.connect(self._on_connection_changed)
            self.serial_controller.log_message.connect(self._append_arduino_log)

    def _init_components(self):
        """初始化核心组件"""
        self.titration_plotter = create_titration_plotter(
            self.ui.titration_curve_plot
        )
        
        self._data_x = []
        self._data_y = []
        self._raw_s1_list = []
        self._raw_s2_list = []
        self._last_s1 = 0
        self._last_s2 = 0
        self._analysis_done = False
        self._time_list = []
        self.start_time = time.time()
        
        self._curve = self.ui.titration_curve_plot.plot(
            pen=pg.mkPen(color=AppConfig.PLOT_COLOR_RGB, width=2),
            symbol='o',
            symbolSize=max(8, AppConfig.PLOT_SYMBOL_SIZE),
            symbolBrush=pg.mkBrush(*AppConfig.PLOT_COLOR_RGB),
            symbolPen=pg.mkPen(*AppConfig.PLOT_COLOR_RGB)
        )
        
        try:
            plot_item = self.ui.titration_curve_plot.getPlotItem()
            self._hover_line = pg.InfiniteLine(
                angle=90, 
                movable=False,
                pen=pg.mkPen(color=(200, 0, 0), style=QtCore.Qt.DashLine)
            )
            plot_item.addItem(self._hover_line, ignoreBounds=True)
            self._hover_line.hide()

            self._selection_lines = []
            self._selected_times = []
            self._selection_mode_active = False

            scene = self.ui.titration_curve_plot.scene()
            scene.sigMouseMoved.connect(self._on_plot_mouse_move)
            scene.sigMouseClicked.connect(self._on_plot_mouse_click)
        except Exception:
            pass
            
        try:
            top_axis = self.ui.titration_curve_plot.getPlotItem().getAxis('top')
            if hasattr(top_axis, 'set_mapping'):
                top_axis.set_mapping(
                    lambda: list(self._time_list), 
                    lambda: list(self._data_x)
                )
        except Exception:
            pass
    
    def _setup_ui_connections(self):
        """设置UI事件连接"""
        self.ui.browse_folder_btn.clicked.connect(self._browse_save_folder)
        self.ui.refresh_ports_btn.clicked.connect(self._refresh_ports)
        self.ui.connect_btn.clicked.connect(self._toggle_connect)
        
        motor_connections = [
            (self.ui.stepper1_forward_button, self._m1_forward),
            (self.ui.stepper1_back_button, self._m1_backward),
            (self.ui.stepper2_forward_button, self._m2_forward),
            (self.ui.stepper2_back_button, self._m2_backward),
            (self.ui.stepper1_stop_button, self._m1_stop),
            (self.ui.stepper2_stop_button, self._m2_stop),
        ]
        for button, handler in motor_connections:
            button.clicked.connect(handler)
        
        self.ui.start_button.clicked.connect(self._start_titration)
        self.ui.stop_plot_button.clicked.connect(self._on_pause_plot)
        self.ui.save_data_button.clicked.connect(self._save_data)
        self.ui.analyze_button.clicked.connect(self._perform_analysis)
        self.ui.save_analysis_button.clicked.connect(self._save_analysis_result)
    
    def _init_timer(self):
        """初始化定时器"""
        self._simulation_timer = QtCore.QTimer(self)
        self._simulation_timer.setInterval(AppConfig.SIMULATION_INTERVAL_MS)
        self._simulation_timer.timeout.connect(self._poll_simulation)
    # endregion

    #region ---------- 基础工具 ----------
    def _append_output(self, text: str):
        self.ui.output.append(text)

    def _append_arduino_log(self, text: str):
        # 将Arduino日志输出到UI
        # self.ui._append_output(text)
        pass

    def _apply_axes_limits(self):
        """设置坐标轴范围"""
        vb = self.ui.titration_curve_plot.getPlotItem().getViewBox()
        if getattr(AppConfig, 'X_AXIS_LIMIT_ENABLED', False):
            vb.setXRange(*AppConfig.X_AXIS_RANGE, padding=0)
        else:
            x_source = None
            if hasattr(self, '_time_list') and self._time_list:
                x_source = self._time_list
            elif hasattr(self, '_data_x') and self._data_x:
                x_source = self._data_x

            if x_source and len(x_source) > 0:
                x_min, x_max = min(x_source), max(x_source)
                x_range = x_max - x_min
                if x_range > 0:
                    x_margin = max(0.5, x_range * 0.05)
                    x_left = max(0, x_min - x_margin)
                    x_right = x_max + x_margin
                    vb.setXRange(x_left, x_right, padding=0)
                else:
                    vb.setXRange(max(0, x_min - 1), x_min + 1, padding=0)
            else:
                vb.setXRange(*AppConfig.X_AXIS_RANGE, padding=0)
        
        if self._data_y:
            y_min, y_max = min(self._data_y), max(self._data_y)
            y_range = y_max - y_min
            
            if y_range > 0:
                margin = y_range * AppConfig.Y_AXIS_MARGIN_RATIO
                vb.setYRange(y_min - margin, y_max + margin, padding=0)
            else:
                vb.setYRange(y_min - 10, y_min + 10, padding=0)
        else:
            vb.setYRange(*AppConfig.DEFAULT_Y_RANGE, padding=0)

    # endregion

    #region ---------- 文件保存 ----------
    def _browse_save_folder(self):
        """浏览保存文件夹"""
        from PyQt5.QtWidgets import QFileDialog

        # 获取当前显示的文件夹路径
        current_folder = self.ui.save_folder_display.text()
        if not os.path.exists(current_folder):
            current_folder = os.getcwd()
        
        # 打开文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self.ui, 
            "选择保存文件夹", 
            current_folder
        )

        if folder_path:
            self.ui.save_folder_display.setText(folder_path)
            self._append_output(f"已设置保存文件夹: {folder_path}")

    def _get_save_path(self) -> Optional[str]:
        """获取完整的保存文件路径"""
        # 获取并验证保存文件夹
        save_folder = (
            self.ui.save_folder_display.text().strip() 
            or AppConfig.DEFAULT_RESULTS_FOLDER
        )
        os.makedirs(save_folder, exist_ok=True)
        # 生成文件名
        filename = self._generate_filename()
        return os.path.join(save_folder, filename)

    def _generate_filename(self, prefix: str = "titration") -> str:
        """生成保存文件名"""
        filename = self.ui.filename_input.text().strip()
        # 当用户未手动填写时，生成时间戳名称
        if not filename or filename.lower() == 'default':
            timestamp = time.strftime(AppConfig.FILENAME_TIME_FORMAT)
            filename = f"{prefix}_{timestamp}"
        else:
            # 用户填写了文件名，直接使用（但加上前缀用于区分类型）
            if prefix != "titration":
                filename = f"{prefix}_{filename}"
        
        # 确保有正确的扩展名
        if not filename.endswith(AppConfig.FILE_EXTENSION):
            filename += AppConfig.FILE_EXTENSION
            
        return filename
    # endregion

    #region ---------- 串口控制 ----------
    def _refresh_ports(self):
        """刷新端口列表"""
        self.ui.port_combo.clear()
        
        if self.serial_controller:
            ports = self.serial_controller.get_available_ports()
            for port in ports:
                self.ui.port_combo.addItem(port)
        else:
            self.ui.port_combo.addItem("串口控制器未加载")

    def _toggle_connect(self):
        """切换连接状态"""
        if not self.serial_controller:
            self._append_output("串口控制器未加载")
            return
            
        port = self.ui.port_combo.currentText().strip()
        
        # 如果已连接，则断开
        if self.serial_controller.is_connected():
            self.serial_controller.disconnect_port()
            self._simulation_timer.stop()
            self._data_generator = None
            return
            
        # 连接到选定端口
        success = self.serial_controller.connect_port(port)
        if success and port == "模拟数据":
            # 启动模拟数据定时器
            self._simulation_timer.start()

    def _on_connection_changed(self, connected: bool, status: str):
        """处理连接状态变化"""
        self.ui.serial_status.setText(status)
        if connected:
            self.ui.serial_status.setStyleSheet("color:#0a0;")
            self.ui.connect_btn.setText("断开")
        else:
            self.ui.serial_status.setStyleSheet("color:#a00;")
            self.ui.connect_btn.setText("连接")

    def _on_serial_data(self, data: dict):
        """处理串口数据"""
        data_type = data.get('type')
        
        if data_type == 'titration_stop':
            pass
        else:
            # 普通数据：包含电机速度和电导率
            motor1 = data.get('motor1', 0)
            motor2 = data.get('motor2', 0)
            conductivity = data.get('conductivity', 0.0)
            
            self._last_s1, self._last_s2 = motor1, motor2
            
            self.ui.stepper1_speed_label.setText(f"当前速度: {motor1}")
            self.ui.stepper2_speed_label.setText(f"当前速度: {motor2}")

            if not getattr(self, '_plot_paused', False):
                self._append_measure(motor1, motor2, conductivity)

    def _poll_simulation(self):
        """轮询模拟数据"""
        if self._data_generator:
            data = self._data_generator.get_next_data()
            if data:
                s1, s2, cond = data
                self._on_serial_data({
                    'motor1': s1,
                    'motor2': s2,
                    'conductivity': cond
                })
            elif self._data_generator.is_finished():
                if not self._analysis_done:
                    self._append_output("Titration stop")
                    self._on_serial_data({'type': 'titration_stop'})
                self._data_generator = None
    # endregion

    #region ---------- 数据与绘图 ----------
    def _append_measure(self, s1: float, s2: float, cond: float):
        """添加测量数据点"""
        if self.ui.max_speed_input is not None:
            time_elapsed = time.time() - self.start_time
            max_sp = float(self.ui.max_speed_input.value())
            
            # 归一化速度
            x_plot = float(s1) / max_sp if max_sp > 0 else 0.0
            
            self._data_x.append(x_plot)
            self._data_y.append(float(cond))
            self._time_list.append(time_elapsed)
            self._raw_s1_list.append(float(s1))
            self._raw_s2_list.append(float(s2))
            
            self._update_plot()
    
    def _update_plot(self):
        """更新绘图显示"""
        try:
            self._curve.setData(self._time_list, self._data_y)
        except Exception:
            self._curve.setData(list(range(len(self._data_y))), self._data_y)
        self._apply_axes_limits()
    
    def _on_pause_plot(self):
        """处理停止绘图按钮点击"""
        self._plot_paused = True
        self._append_output("绘图已停止")

    def _save_data(self):
        """保存原始数据"""
        user_folder = self.ui.save_folder_display.text().strip()
        if not user_folder:
            user_folder = AppConfig.DEFAULT_RESULTS_FOLDER

        user_folder = os.path.expanduser(user_folder)
        if not os.path.isabs(user_folder):
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')
            )
            save_folder = os.path.abspath(
                os.path.join(project_root, user_folder)
            )
        else:
            save_folder = os.path.abspath(user_folder)

        raw_dir = os.path.join(save_folder, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        filename = self._generate_filename("raw")
        path = os.path.join(raw_dir, filename)

        n = min(
            len(self._time_list),
            len(self._data_y),
            len(self._data_x),
            len(self._raw_s1_list),
            len(self._raw_s2_list),
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(
                'time_s,conductivity,motor1_proportion,motor1_speed,motor2_speed\n'
            )
            for i in range(n):
                t = self._time_list[i]
                cond = self._data_y[i]
                prop = self._data_x[i]
                s1 = self._raw_s1_list[i]
                s2 = self._raw_s2_list[i]
                f.write(f"{t:.4f},{cond:.6f},{prop:.6f},{s1:.4f},{s2:.4f}\n")

        self._append_output(f"已保存原始数据: {path}")

    def _perform_analysis(self):
        """点击分析按钮：激活选择模式，等待用户选择两个位置"""
        if not self._data_x or not self._data_y:
            self._append_output("没有数据可供分析")
            return
            
        # 清除之前的选择
        self._clear_selections()
        
        # 激活选择模式
        self._selection_mode_active = True
        self._append_output("请在图上点击选择两个位置来定义分析范围...")
    
    def _clear_selections(self):
        """清除所有选择线和状态"""
        try:
            plot_item = self.ui.titration_curve_plot.getPlotItem()
            for ln in self._selection_lines:
                try:
                    plot_item.removeItem(ln)
                except Exception:
                    pass
            self._selection_lines = []
            self._selected_times = []
        except Exception:
            pass
    
    def _execute_analysis_with_selection(self):
        """使用选择的范围执行分析"""
        self._append_output("开始分析选定范围的数据...")

        # 将所选的 time 坐标映射为 proportion（线性插值）
        def time_to_prop(t):
            if not self._time_list or not self._data_x:
                return None
            pairs = sorted(
                zip(self._time_list, self._data_x), 
                key=lambda p: p[0]
            )
            xp = [p[0] for p in pairs]
            fp = [p[1] for p in pairs]
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

        t1, t2 = self._selected_times
        p1 = time_to_prop(t1)
        p2 = time_to_prop(t2)
        if p1 is None or p2 is None:
            self._append_output(
                "选择无效：当前无数据用于映射 time->proportion"
            )
            return

        pmin, pmax = min(p1, p2), max(p1, p2)
        filtered_x, filtered_y = [], []
        for prop, y in zip(self._data_x, self._data_y):
            if pmin <= prop <= pmax:
                filtered_x.append(prop)
                filtered_y.append(y)
        
        if len(filtered_x) < 8:
            self._append_output(
                f"所选范围数据点太少 ({len(filtered_x)})，需要至少 8 个点"
            )
            return

        # 准备保存路径
        user_folder = (
            self.ui.save_folder_display.text().strip() 
            or AppConfig.DEFAULT_RESULTS_FOLDER
        )
        user_folder = os.path.expanduser(user_folder)
        if not os.path.isabs(user_folder):
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')
            )
            user_folder = os.path.abspath(
                os.path.join(project_root, user_folder)
            )
        processed_dir = os.path.join(user_folder, 'processed')
        try:
            os.makedirs(processed_dir, exist_ok=True)
        except Exception:
            self._append_output(f"无法创建 processed 目录: {processed_dir}")
            return

        filename = self._generate_filename()
        # 只传递目录路径，让 analyze_titration_from_curve 自己生成文件名
        
        try:
            result_dict = analyze_titration_from_curve(
                x=filtered_x,
                y=filtered_y,
                hcl_conc=self.ui.c_hcl_input.value(),
                save_txt_path=processed_dir,
                filename=filename
            )
            
            # 记录并显示分析结果
            self._last_analysis_result = result_dict
            self._update_analysis_results(result_dict)
            
            # 检查保存路径
            saved_path = (
                result_dict.get('_saved_txt_path') 
                if isinstance(result_dict, dict) 
                else None
            )
            if saved_path and os.path.exists(saved_path):
                self._append_output(f"分析结果已保存: {saved_path}")
            else:
                # 回退保存
                try:
                    summary_text = self.titration_plotter.get_analysis_summary_text(
                        result_dict
                    )
                    fallback_name = (
                        f"analysis_fallback_"
                        f"{time.strftime(AppConfig.FILENAME_TIME_FORMAT)}"
                        f"{AppConfig.FILE_EXTENSION}"
                    )
                    fallback_path = os.path.join(processed_dir, fallback_name)
                    with open(fallback_path, 'w', encoding='utf-8') as f:
                        f.write(summary_text)
                    self._append_output(
                        f"分析结果（回退）已保存: {fallback_path}"
                    )
                    result_dict['_saved_txt_path'] = fallback_path
                except Exception as e:
                    self._append_output(f"分析结果保存失败: {e}")
            
            # 绘制分析结果
            filtered_times = []
            for prop, y, t in zip(self._data_x, self._data_y, self._time_list):
                if pmin <= prop <= pmax:
                    filtered_times.append(t)
            
            if len(filtered_times) == len(filtered_x):
                self.titration_plotter.plot_analysis_results(
                    result_dict, filtered_y, filtered_times, filtered_x
                )
            else:
                self.titration_plotter.plot_analysis_results(
                    result_dict, filtered_y, self._time_list, self._data_x
                )

            # 显示分析摘要
            summary_text = self.titration_plotter.get_analysis_summary_text(
                result_dict
            )
            self._append_output(summary_text)
            
        except Exception as e:
            self._append_output(f"分析失败: {e}")

    def _save_analysis_result(self):
        """保存最近一次分析结果"""
        if (not hasattr(self, '_last_analysis_result') 
            or not self._last_analysis_result):
            self._append_output("没有找到分析结果，正在尝试先执行分析...")
            self._perform_analysis()
            if (not hasattr(self, '_last_analysis_result') 
                or not self._last_analysis_result):
                self._append_output("无法生成分析结果，取消保存。")
                return

        save_folder = (
            self.ui.save_folder_display.text().strip() 
            or AppConfig.DEFAULT_RESULTS_FOLDER
        )
        save_folder = os.path.expanduser(save_folder)
        if not os.path.isabs(save_folder):
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')
            )
            save_folder = os.path.abspath(
                os.path.join(project_root, save_folder)
            )
        processed_dir = os.path.join(save_folder, 'processed')
        os.makedirs(processed_dir, exist_ok=True)
        filename = self._generate_filename("analysis")
        path = os.path.join(processed_dir, filename)

        try:
            summary_text = self.titration_plotter.get_analysis_summary_text(
                self._last_analysis_result
            )
            with open(path, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            self._append_output(f"分析结果已保存: {path}")
        except Exception as e:
            self._append_output(f"保存分析结果失败: {e}")

    def _clear_plot(self):
        """清空绘图和相关显示"""
        self._data_x.clear()
        self._data_y.clear()
        self._time_list.clear()
        self._raw_s1_list.clear()
        self._raw_s2_list.clear()
        self._analysis_done = False
        self._update_plot()
        self.titration_plotter.clear_fit_items()
    
    def _update_analysis_results(self, result_dict: dict):
        """更新分析结果显示"""
        c_naoh = result_dict.get('NaOH_conc')
        if c_naoh is not None:
            if hasattr(self.ui, 'naoh_label'):
                self.ui.naoh_label.setText(
                    f"c(NaOH): {c_naoh:.4f} mol/L"
                )

    def _on_plot_mouse_move(self, ev):
        """鼠标移动事件处理"""
        try:
            if not getattr(self, '_selection_mode_active', False):
                self._hover_line.hide()
                return
                
            pos = ev
            plot_item = self.ui.titration_curve_plot.getPlotItem()
            vb = plot_item.getViewBox()
            mouse_point = vb.mapSceneToView(pos)
            x = mouse_point.x()
            xr = vb.viewRange()[0]
            if xr[0] <= x <= xr[1]:
                self._hover_line.setPos(x)
                self._hover_line.show()
            else:
                self._hover_line.hide()
        except Exception:
            pass

    def _on_plot_mouse_click(self, ev):
        """鼠标点击事件处理"""
        try:
            if ev.button() != QtCore.Qt.LeftButton:
                return
                
            if not getattr(self, '_selection_mode_active', False):
                return
                
            scene_pos = ev.scenePos()
            plot_item = self.ui.titration_curve_plot.getPlotItem()
            vb = plot_item.getViewBox()
            mouse_point = vb.mapSceneToView(scene_pos)
            x = mouse_point.x()

            if len(self._selected_times) >= 2:
                for ln in self._selection_lines:
                    try:
                        plot_item.removeItem(ln)
                    except Exception:
                        pass
                self._selection_lines = []
                self._selected_times = []

            sel_line = pg.InfiniteLine(
                pos=x, 
                angle=90, 
                movable=False,
                pen=pg.mkPen(color=(200, 0, 0), width=2)
            )
            plot_item.addItem(sel_line)
            self._selection_lines.append(sel_line)
            self._selected_times.append(x)

            if len(self._selected_times) == 1:
                self._append_output(
                    f"已选定第1个位置 (time={x:.4f})，请选择第2个位置"
                )
            elif len(self._selected_times) == 2:
                self._append_output(
                    f"已选定第2个位置 (time={x:.4f})，开始执行分析..."
                )
                self._selection_mode_active = False
                self._execute_analysis_with_selection()
        except Exception:
            pass
    # endregion

    #region ---------- 电机控制 ----------
    def _control_motor(self, motor_id: int, action: str, speed: int = None):
        """通用电机控制方法"""
        if not self.serial_controller:
            return False
            
        # 获取对应的UI组件
        speed_input = getattr(
            self.ui, f'stepper{motor_id}_speed_input', None
        )
        speed_label = getattr(
            self.ui, f'stepper{motor_id}_speed_label', None
        )
        
        if not speed_input or not speed_label:
            return False
            
        # 执行动作
        if action == 'forward':
            sp = speed or int(speed_input.value())
            success = self.serial_controller.motor_forward(motor_id, sp)
            display_speed = sp
        elif action == 'backward':
            sp = speed or int(speed_input.value())
            success = self.serial_controller.motor_backward(motor_id, sp)
            display_speed = -sp
        elif action == 'stop':
            success = self.serial_controller.motor_stop(motor_id)
            display_speed = 0
        else:
            return False
            
        # 更新界面显示
        if success:
            speed_label.setText(f"当前速度: {display_speed}")
        return success

    def _m1_forward(self):
        """电机1正转"""
        self._control_motor(1, 'forward')

    def _m1_backward(self):
        """电机1反转"""
        self._control_motor(1, 'backward')

    def _m2_forward(self):
        """电机2正转"""
        self._control_motor(2, 'forward')

    def _m2_backward(self):
        """电机2反转"""
        self._control_motor(2, 'backward')

    def _m1_stop(self):
        """停止电机1"""
        self._control_motor(1, 'stop')

    def _m2_stop(self):
        """停止电机2"""
        self._control_motor(2, 'stop')

    def _start_titration(self):
        """开始滴定"""
        max_sp = int(self.ui.max_speed_input.value())
        inc_ms = int(self.ui.increment_rounds_input.value())

        # 清空曲线数据，准备新一轮滴定
        self._clear_plot()
        self._append_output("旧图已清除")

        # 清除旧拟合
        self.titration_plotter.clear_fit_items()
        self._append_output("旧拟合已清除")

        # 清除时间
        self._time_list = []
        self.start_time = time.time()
            
        self._append_output("开始滴定")
        
        # 检查是否为模拟模式
        current_port = self.ui.port_combo.currentText().strip()
        if current_port == "模拟数据":
            # 模拟模式：通过串口控制器播放已加载的模拟文件
            if self.serial_controller:
                try:
                    self.serial_controller.start_simulation(reset=True)
                    self._plot_paused = False
                    self._append_output("已启动模拟数据播放")
                except Exception as e:
                    self._append_output(f"启动模拟数据失败: {e}")
            else:
                if TitrationSimulator:
                    self._data_generator = TitrationSimulator(max_sp, inc_ms)
                else:
                    self._append_output(
                        "错误：无法加载 TitrationSimulator 模块，"
                        "且串口控制器不可用"
                    )
        else:
            # 真实串口模式：发送命令
            if self.serial_controller:
                self.serial_controller.start_titration(max_sp, inc_ms)
    #endregion


def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainForm()
    controller = AppController(window)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
