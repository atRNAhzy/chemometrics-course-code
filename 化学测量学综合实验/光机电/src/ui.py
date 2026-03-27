from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg


class ResponsiveFontManager:
    """响应式字体管理器，根据窗口大小调整字体"""
    
    def __init__(self, widget):
        self.widget = widget
        self.base_width = 2000  # 基准窗口宽度
        self.base_height = 1800  # 基准窗口高度
        self.base_title_size = 12  # 基准标题字体大小
        self.base_body_size = 11   # 基准正文字体大小
        
        # 存储所有需要响应式调整的组件
        self.title_components = []
        self.body_components = []
        
    def add_title_component(self, component):
        """添加标题组件"""
        self.title_components.append(component)
        
    def add_body_component(self, component):
        """添加正文组件"""
        self.body_components.append(component)
        
    def update_fonts(self):
        """根据当前窗口大小更新所有字体"""
        current_size = self.widget.size()
        
        # 计算缩放比例（取宽高比例的平均值，避免过度变化）
        width_ratio = current_size.width() / self.base_width
        height_ratio = current_size.height() / self.base_height
        scale_ratio = (width_ratio + height_ratio) / 2
        
        # 限制缩放比例在合理范围内
        scale_ratio = max(0.5, min(scale_ratio, 3.0))
        
        # 计算新的字体大小
        new_title_size = max(8, int(self.base_title_size * scale_ratio))
        new_body_size = max(7, int(self.base_body_size * scale_ratio))
        
        # 更新标题字体
        title_font = QtGui.QFont()
        title_font.setPointSize(new_title_size)
        title_font.setBold(True)
        
        for component in self.title_components:
            if hasattr(component, 'setFont'):
                component.setFont(title_font)
                
        # 更新正文字体
        body_font = QtGui.QFont()
        body_font.setPointSize(new_body_size)
        
        for component in self.body_components:
            if hasattr(component, 'setFont'):
                component.setFont(body_font)

class PercentAxisItem(pg.AxisItem):
    """自定义百分比刻度轴（0..1 显示为 0%..100%）"""

    def tickStrings(self, values, scale, spacing):
        try:
            return [f"{int(round(v * 100))}%" for v in values]
        except Exception:
            return super().tickStrings(values, scale, spacing)

class ProportionTopAxis(pg.AxisItem):
    """顶部轴：根据时间轴的刻度值，在给定的 time->proportion 对上插值并显示 m1 比例"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 回调函数，用于获取最新数据列表
        self._get_time = lambda: []
        self._get_prop = lambda: []

    def set_mapping(self, get_time_cb, get_prop_cb):
        """设置回调：get_time_cb() -> list of times, get_prop_cb() -> list of proportions"""
        self._get_time = get_time_cb
        self._get_prop = get_prop_cb

    def _interp(self, x, xp, fp):
        # 简单线性插值，不依赖 numpy；假定 xp,fp 已排序按 xp
        if not xp or not fp:
            return 0.0
        if x <= xp[0]:
            return fp[0]
        if x >= xp[-1]:
            return fp[-1]
        # 找段
        for i in range(len(xp) - 1):
            if xp[i] <= x <= xp[i+1]:
                x0, x1 = xp[i], xp[i+1]
                y0, y1 = fp[i], fp[i+1]
                if x1 == x0:
                    return y0
                t = (x - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
        return fp[-1]

    def tickStrings(self, values, scale, spacing):
        try:
            times = list(self._get_time() or [])
            props = list(self._get_prop() or [])
            if not times or not props or len(times) != len(props):
                # 无效数据时显示空白（避免误导）
                return ["" for _ in values]

            # 排序数据对以确保 xp 单调递增
            pairs = sorted(zip(times, props), key=lambda x: x[0])
            xp = [p[0] for p in pairs]
            fp = [p[1] for p in pairs]

            out = []
            for v in values:
                prop_v = self._interp(v, xp, fp)
                out.append(f"{prop_v:.3f}")
            return out
        except Exception:
            return super().tickStrings(values, scale, spacing)

class MainForm(QtWidgets.QWidget):
    """仅负责 UI 结构的窗口类，不包含业务逻辑。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font_manager = ResponsiveFontManager(self)
        self._build_ui()
        
    def resizeEvent(self, event):
        """窗口大小改变时的响应"""
        super().resizeEvent(event)
        # 延迟更新字体，避免频繁调整
        QtCore.QTimer.singleShot(100, self.font_manager.update_fonts)

    def _build_ui(self):
        self.setObjectName("Form")
        self.resize(2000, 1600)

        # 顶层网格布局（响应式）
        self.mainLayout = QtWidgets.QGridLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setHorizontalSpacing(12)
        self.mainLayout.setVerticalSpacing(12)

        # 字体（初始设置，后续由响应式管理器控制）
        title_font = QtGui.QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        body_font = QtGui.QFont()
        body_font.setPointSize(11)

        # 左列：串口 + 控制面板（两块）
        self.leftPanel = QtWidgets.QVBoxLayout()
        self.leftPanel.setSpacing(14)

        # 文件保存区
        saveGroup = QtWidgets.QGroupBox("文件保存")
        saveGroup.setFont(title_font)
        self.font_manager.add_title_component(saveGroup)
        saveLayout = QtWidgets.QGridLayout(saveGroup)
        saveLayout.setContentsMargins(10, 10, 10, 10)
        saveLayout.setHorizontalSpacing(8)
        saveLayout.setVerticalSpacing(8)

        # 第一步：保存文件夹选择
        folder_label = QtWidgets.QLabel("保存文件夹")
        folder_label.setFont(body_font)
        self.font_manager.add_body_component(folder_label)
        
        self.save_folder_display = QtWidgets.QLineEdit("results")
        self.save_folder_display.setFont(body_font)
        self.save_folder_display.setReadOnly(True)  # 只读，不可编辑
        self.save_folder_display.setStyleSheet("background-color: #f0f0f0; padding: 4px; border: 1px solid #ccc;")
        self.font_manager.add_body_component(self.save_folder_display)
        
        self.browse_folder_btn = QtWidgets.QPushButton("浏览文件夹")
        self.browse_folder_btn.setFont(body_font)
        self.font_manager.add_body_component(self.browse_folder_btn)
        
        # 第二步：文件名输入
        filename_label = QtWidgets.QLabel("文件名")
        filename_label.setFont(body_font)
        self.font_manager.add_body_component(filename_label)
        
        self.filename_input = QtWidgets.QLineEdit()
        self.filename_input.setFont(body_font)
        # 不在初始化时显示真实时间戳，使用占位符 'default'
        self.filename_input.setText("default")
        self.filename_input.setPlaceholderText("输入文件名（不含扩展名）")
        self.font_manager.add_body_component(self.filename_input)
        
        # 布局安排
        # 第0行：保存文件夹标签和浏览按钮
        saveLayout.addWidget(folder_label, 0, 0)
        saveLayout.addWidget(self.browse_folder_btn, 0, 2)
        # 第1行：路径显示（单独一行）
        saveLayout.addWidget(self.save_folder_display, 1, 0, 1, 3)
        # 第2行：文件名标签
        saveLayout.addWidget(filename_label, 2, 0, 1, 3)
        # 第3行：文件名输入框
        saveLayout.addWidget(self.filename_input, 3, 0, 1, 3)

        self.leftPanel.addWidget(saveGroup)

        # 串口连接区
        serialGroup = QtWidgets.QGroupBox("串口")
        serialGroup.setFont(title_font)
        self.font_manager.add_title_component(serialGroup)
        serialLayout = QtWidgets.QGridLayout(serialGroup)
        serialLayout.setContentsMargins(10, 10, 10, 10)
        serialLayout.setHorizontalSpacing(8)
        serialLayout.setVerticalSpacing(8)

        port_label = QtWidgets.QLabel("端口")
        port_label.setFont(body_font)
        self.font_manager.add_body_component(port_label)
        
        self.port_combo = QtWidgets.QComboBox()
        self.port_combo.setFont(body_font)
        self.font_manager.add_body_component(self.port_combo)
        
        self.refresh_ports_btn = QtWidgets.QPushButton("刷新")
        self.refresh_ports_btn.setFont(body_font)
        self.font_manager.add_body_component(self.refresh_ports_btn)
        
        self.connect_btn = QtWidgets.QPushButton("连接")
        self.connect_btn.setFont(body_font)
        self.font_manager.add_body_component(self.connect_btn)
        
        self.serial_status = QtWidgets.QLabel("未连接")
        self.serial_status.setFont(body_font)
        self.serial_status.setStyleSheet("color: #a00;")
        self.font_manager.add_body_component(self.serial_status)

        serialLayout.addWidget(port_label, 0, 0)
        serialLayout.addWidget(self.port_combo, 0, 1)
        serialLayout.addWidget(self.refresh_ports_btn, 0, 2)
        serialLayout.addWidget(self.connect_btn, 1, 0)
        serialLayout.addWidget(self.serial_status, 1, 1, 1, 2)

        self.leftPanel.addWidget(serialGroup)

        # 电机控制
        motorGroup = QtWidgets.QGroupBox("电机控制")
        motorGroup.setFont(title_font)
        self.font_manager.add_title_component(motorGroup)
        motorLayout = QtWidgets.QGridLayout(motorGroup)
        motorLayout.setContentsMargins(10, 10, 10, 10)
        motorLayout.setHorizontalSpacing(12)
        motorLayout.setVerticalSpacing(10)

        # 电机1
        self.stepper1_control_box = QtWidgets.QLabel("电机 1")
        self.stepper1_control_box.setFont(title_font)
        self.font_manager.add_title_component(self.stepper1_control_box)
        
        self.stepper1_speed_input = QtWidgets.QSpinBox()
        self.stepper1_speed_input.setRange(0, 200000)
        self.stepper1_speed_input.setSingleStep(1000)  # 步进值设为1000
        self.stepper1_speed_input.setFont(body_font)
        self.stepper1_speed_input.setMinimumWidth(90)
        self.stepper1_speed_input.setValue(10000)
        self.font_manager.add_body_component(self.stepper1_speed_input)
        
        self.stepper1_forward_button = QtWidgets.QPushButton("前进")
        self.stepper1_back_button = QtWidgets.QPushButton("后退")
        self.stepper1_stop_button = QtWidgets.QPushButton("停止")
        for b in (self.stepper1_forward_button, self.stepper1_back_button, self.stepper1_stop_button):
            b.setFont(body_font)
            b.setMinimumHeight(32)
            self.font_manager.add_body_component(b)

        # 电机2
        self.stepper2_text = QtWidgets.QLabel("电机 2")
        self.stepper2_text.setFont(title_font)
        self.font_manager.add_title_component(self.stepper2_text)
        
        self.stepper2_speed_input = QtWidgets.QSpinBox()
        self.stepper2_speed_input.setRange(0, 200000)
        self.stepper2_speed_input.setSingleStep(1000)  # 步进值设为1000
        self.stepper2_speed_input.setFont(body_font)
        self.stepper2_speed_input.setMinimumWidth(90)
        self.stepper2_speed_input.setValue(10000)
        self.font_manager.add_body_component(self.stepper2_speed_input)
        
        self.stepper2_forward_button = QtWidgets.QPushButton("前进")
        self.stepper2_back_button = QtWidgets.QPushButton("后退")
        self.stepper2_stop_button = QtWidgets.QPushButton("停止")
        for b in (self.stepper2_forward_button, self.stepper2_back_button, self.stepper2_stop_button):
            b.setFont(body_font)
            b.setMinimumHeight(32)
            self.font_manager.add_body_component(b)

        # 电机区域布局：两列
        motorLayout.addWidget(
            self.stepper1_control_box, 0, 0, 1, 1, QtCore.Qt.AlignHCenter)
        motorLayout.addWidget(
            self.stepper2_text, 0, 1, 1, 1, QtCore.Qt.AlignHCenter)
        motorLayout.addWidget(self.stepper1_speed_input,  1, 0)
        motorLayout.addWidget(self.stepper2_speed_input,  1, 1)
        # 动态显示点击速度的标签
        self.stepper1_speed_label = QtWidgets.QLabel("当前速度: 0")
        self.stepper1_speed_label.setFont(body_font)
        self.font_manager.add_body_component(self.stepper1_speed_label)
        
        self.stepper2_speed_label = QtWidgets.QLabel("当前速度: 0")
        self.stepper2_speed_label.setFont(body_font)
        self.font_manager.add_body_component(self.stepper2_speed_label)
        motorLayout.addWidget(self.stepper1_speed_label, 2, 0)
        motorLayout.addWidget(self.stepper2_speed_label, 2, 1)
        motorLayout.addWidget(self.stepper1_forward_button, 3, 0)
        motorLayout.addWidget(self.stepper2_forward_button, 3, 1)
        motorLayout.addWidget(self.stepper1_back_button, 4, 0)
        motorLayout.addWidget(self.stepper2_back_button, 4, 1)
        motorLayout.addWidget(self.stepper1_stop_button, 5, 0)
        motorLayout.addWidget(self.stepper2_stop_button, 5, 1)

        # 滴定参数
        self.titration_config_box = QtWidgets.QGroupBox("滴定参数")
        self.titration_config_box.setFont(title_font)
        self.font_manager.add_title_component(self.titration_config_box)
        configLayout = QtWidgets.QGridLayout(self.titration_config_box)
        configLayout.setContentsMargins(10, 10, 10, 10)
        configLayout.setHorizontalSpacing(12)
        configLayout.setVerticalSpacing(10)

        self.max_speed = QtWidgets.QLabel("最大速度")
        self.max_speed.setFont(body_font)
        self.font_manager.add_body_component(self.max_speed)
        
        self.c_hcl_text = QtWidgets.QLabel("c(HCL)")
        self.c_hcl_text.setFont(body_font)
        self.font_manager.add_body_component(self.c_hcl_text)

        self.max_speed_input = QtWidgets.QSpinBox()
        self.max_speed_input.setRange(0, 200000)
        self.max_speed_input.setSingleStep(1000)  # 步进值设为1000
        self.max_speed_input.setFont(body_font)
        self.max_speed_input.setMinimumWidth(90)
        self.max_speed_input.setValue(3000)
        self.font_manager.add_body_component(self.max_speed_input)

        self.c_hcl_input = QtWidgets.QDoubleSpinBox()
        self.c_hcl_input.setRange(0.0, 10.0)
        self.c_hcl_input.setDecimals(3)
        self.c_hcl_input.setSingleStep(0.01)
        self.c_hcl_input.setFont(body_font)
        self.c_hcl_input.setMinimumWidth(90)
        self.c_hcl_input.setValue(0.2)
        self.font_manager.add_body_component(self.c_hcl_input)

        self.increment_rounds = QtWidgets.QLabel("递增时间")
        self.increment_rounds.setFont(body_font)
        self.font_manager.add_body_component(self.increment_rounds)
        
        self.increment_rounds_input = QtWidgets.QSpinBox()
        self.increment_rounds_input.setRange(0, 100000)
        self.increment_rounds_input.setFont(body_font)
        self.increment_rounds_input.setMinimumWidth(90)
        self.increment_rounds_input.setValue(10)
        self.font_manager.add_body_component(self.increment_rounds_input)

        # 按钮：第一行（开始，停止绘图，保存数据），第二行（数据分析，保存分析结果）
        self.start_button = QtWidgets.QPushButton("开始")
        self.start_button.setFont(body_font)
        self.start_button.setMinimumHeight(32)
        self.font_manager.add_body_component(self.start_button)

        # 新增按钮：停止绘图、保存数据、数据分析、保存分析结果
        self.stop_plot_button = QtWidgets.QPushButton("停止绘图")
        self.stop_plot_button.setFont(body_font)
        self.stop_plot_button.setMinimumHeight(32)
        self.font_manager.add_body_component(self.stop_plot_button)

        self.save_data_button = QtWidgets.QPushButton("保存数据")
        self.save_data_button.setFont(body_font)
        self.save_data_button.setMinimumHeight(32)
        self.font_manager.add_body_component(self.save_data_button)

        self.analyze_button = QtWidgets.QPushButton("数据分析")
        self.analyze_button.setFont(body_font)
        self.analyze_button.setMinimumHeight(32)
        self.font_manager.add_body_component(self.analyze_button)

        self.save_analysis_button = QtWidgets.QPushButton("保存分析结果")
        self.save_analysis_button.setFont(body_font)
        self.save_analysis_button.setMinimumHeight(32)
        self.font_manager.add_body_component(self.save_analysis_button)

        configLayout.addWidget(self.max_speed,       0, 0)
        configLayout.addWidget(self.max_speed_input, 0, 1)
        configLayout.addWidget(self.c_hcl_text,      1, 0)
        configLayout.addWidget(self.c_hcl_input,     1, 1)
        configLayout.addWidget(self.increment_rounds,       2, 0)
        configLayout.addWidget(self.increment_rounds_input, 2, 1)
        configLayout.addItem(
            QtWidgets.QSpacerItem(
                10, 6, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed),
            3, 0, 1, 2)

        btnRow1 = QtWidgets.QHBoxLayout()
        btnRow1.setSpacing(10)
        btnRow1.addStretch(1)
        btnRow1.addWidget(self.start_button)
        btnRow1.addWidget(self.stop_plot_button)
        btnRow1.addWidget(self.save_data_button)
        btnRow1.addStretch(1)

        btnRow2 = QtWidgets.QHBoxLayout()
        btnRow2.setSpacing(10)
        btnRow2.addStretch(1)
        btnRow2.addWidget(self.analyze_button)
        btnRow2.addWidget(self.save_analysis_button)
        btnRow2.addStretch(1)

        vbtns = QtWidgets.QVBoxLayout()
        vbtns.addLayout(btnRow1)
        vbtns.addLayout(btnRow2)
        configLayout.addLayout(vbtns, 4, 0, 1, 2)

        # 左列加入两个组
        self.leftPanel.addWidget(motorGroup)
        self.leftPanel.addWidget(self.titration_config_box)

        leftContainer = QtWidgets.QWidget()
        leftContainer.setLayout(self.leftPanel)
        leftContainer.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        leftContainer.setMinimumWidth(300)
        leftContainer.setMaximumWidth(100000)

        # 右列：绘图 + 输出
        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.setSpacing(10)
    
        bottom_axis = pg.AxisItem(orientation='bottom')
        top_axis = ProportionTopAxis(orientation='top')
        # 创建 PlotWidget 并注册顶部与底部轴
        self.titration_curve_plot = pg.PlotWidget(axisItems={'bottom': bottom_axis, 'top': top_axis})
        self.titration_curve_plot.setBackground('w')
        self.titration_curve_plot.showGrid(x=True, y=True, alpha=0.3)
        self.titration_curve_plot.setMinimumHeight(360)
        plot_item = self.titration_curve_plot.getPlotItem()
        for name in ('left', 'bottom', 'top'):
            axis = plot_item.getAxis(name)
            axis.setPen(pg.mkPen(color=(0, 0, 0), width=2))
        plot_item.setLabel('bottom', 'time (s)')
        # 顶部轴默认标签（实际映射由 controller 在运行时设置）
        plot_item.getAxis('top').setLabel('m1 proportion')
        plot_item.setLabel('left', 'Conductivity')

        self.output = QtWidgets.QTextBrowser()
        self.output.setMaximumHeight(400)
        self.output.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        rightLayout.addWidget(self.titration_curve_plot, 4)
        rightLayout.addWidget(self.output, 1)

        rightContainer = QtWidgets.QWidget()
        rightContainer.setLayout(rightLayout)

        # 放入顶层网格：左列固定，右列扩展
        self.mainLayout.addWidget(leftContainer, 0, 0)
        self.mainLayout.addWidget(rightContainer, 0, 1)
        self.mainLayout.setColumnStretch(0, 1)
        self.mainLayout.setColumnStretch(1, 2)
