import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QGraphicsView, QGraphicsScene, QSlider, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QColorDialog, QGridLayout  # 导入表格相关控件
)
from PyQt5.QtGui import QPixmap, QImage, QBrush, QColor, QPen, QLinearGradient, QPalette  # 导入渐变相关控件
from PyQt5.QtCore import Qt, QRectF  # 导入 QRectF
import numpy as np
from PIL import Image, ImageOps, ImageEnhance  # 导入 ImageEnhance 模块
import cv2  # 添加OpenCV库
import scipy.ndimage  # 添加用于中心线提取的库

class ColorExtractorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像颜色提取工具")
        self.setGeometry(100, 100, 600, 600)

        # 初始化Tab管理器
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 添加第一个页面
        self.new_page()

    def new_page(self):
        # 创建新页面
        page = ColorExtractorPage()
        self.tab_widget.addTab(page, f"页面 {self.tab_widget.count() + 1}")

class ColorExtractorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.image_array = None
        self.original_image = None  # 保存原始图片
        self.image_hsv = None
        self.selected_color_hsv = None  # 保存选中的HSV颜色

        # HSV范围
        self.h_range = [0, 255]
        self.s_range = [0, 255]
        self.v_range = [0, 255]

        # 创建UI布局
        self.layout = QVBoxLayout(self)

        # 上传图片按钮
        self.upload_button = QPushButton("上传图片")
        self.upload_button.clicked.connect(self.upload_image)
        self.layout.addWidget(self.upload_button)

        # 创建水平布局用于显示四个区域
        self.image_layout = QHBoxLayout()  # 修改为水平布局
        self.layout.addLayout(self.image_layout)

        # 左侧：显示原始图片
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.mousePressEvent = self.get_pixel_color  # 绑定鼠标点击事件
        self.image_layout.addWidget(self.graphics_view)

        # 中左：显示高亮图片
        self.highlight_view = QGraphicsView()
        self.highlight_scene = QGraphicsScene()
        self.highlight_view.setScene(self.highlight_scene)
        self.image_layout.addWidget(self.highlight_view)

        # 中右：显示二值化图片
        self.binary_view = QGraphicsView()
        self.binary_scene = QGraphicsScene()
        self.binary_view.setScene(self.binary_scene)
        self.image_layout.addWidget(self.binary_view)

        # 右侧：空置
        self.empty_view = QGraphicsView()
        self.image_layout.addWidget(self.empty_view)

        # 显示选中颜色
        self.color_label = QLabel("选中颜色: 无")  # 初始化 self.color_label
        self.color_label.setStyleSheet("background-color: white;")
        self.layout.addWidget(self.color_label)

        # HSV滑块布局
        self.add_hsv_sliders()

        # 计算按钮
        self.calculate_button = QPushButton("计算")
        self.calculate_button.clicked.connect(self.calculate_area)
        self.layout.addWidget(self.calculate_button)

        # 显示面积
        self.area_label = QLabel("符合条件的像素面积: 0")
        self.layout.addWidget(self.area_label)

        # 添加表格
        self.add_table()

        # 添加保存按钮
        self.add_save_buttons()

        self.selected_column = 1  # 默认选中第一列

    def add_hsv_sliders(self):
        # 添加 HSV 滑块
        self.layout.addWidget(QLabel("H范围"))
        self.h_slider_min = self.create_slider(0, 255, 0, self.update_h_range)
        self.h_slider_max = self.create_slider(0, 255, 255, self.update_h_range)
        self.layout.addWidget(self.h_slider_min)
        self.layout.addWidget(self.h_slider_max)

        self.layout.addWidget(QLabel("S范围"))
        self.s_slider_min = self.create_slider(0, 255, 0, self.update_s_range)
        self.s_slider_max = self.create_slider(0, 255, 255, self.update_s_range)
        self.layout.addWidget(self.s_slider_min)
        self.layout.addWidget(self.s_slider_max)

        self.layout.addWidget(QLabel("V范围"))
        self.v_slider_min = self.create_slider(0, 255, 0, self.update_v_range)
        self.v_slider_max = self.create_slider(0, 255, 255, self.update_v_range)
        self.layout.addWidget(self.v_slider_min)
        self.layout.addWidget(self.v_slider_max)

    def create_slider(self, min_val, max_val, init_val, callback):
        # 创建滑块
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(init_val)
        slider.valueChanged.connect(callback)
        return slider

    def update_h_range(self):
        self.h_range = [self.h_slider_min.value(), self.h_slider_max.value()]
        self.calculate_area()

    def update_s_range(self):
        self.s_range = [self.s_slider_min.value(), self.s_slider_max.value()]
        self.calculate_area()

    def update_v_range(self):
        self.v_range = [self.v_slider_min.value(), self.v_slider_max.value()]
        self.calculate_area()

    def upload_image(self):
        # 上传图片
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Image Files (*.jpg *.png *.jpeg)")
        if file_path:
            self.image = Image.open(file_path).convert("RGBA")  # 兼容PNG格式，确保有RGBA通道
            self.image_array = np.array(self.image)
            if self.image_array.shape[2] == 4:  # 如果有透明通道，去掉Alpha通道
                self.image_array = self.image_array[:, :, :3]  # 保留RGB三通道
            self.image = Image.fromarray(self.image_array)  # 更新self.image为三通道图像
            self.original_image = self.image.copy()  # 保存原始图片

            # 转换为HSV并均衡化V通道
            hsv_image = cv2.cvtColor(self.image_array, cv2.COLOR_RGB2HSV)
            hsv_image[:, :, 2] = cv2.equalizeHist(hsv_image[:, :, 2])  # 对V通道均衡化
            self.image_hsv = hsv_image  # 保存均衡化后的HSV图像

            # 转换回RGB以显示均衡化后的图像
            equalized_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
            self.display_image(equalized_image)  # 左上角显示均衡化后的图片

            # 调整视图大小
            self.adjust_view_size()

    def display_image(self, image_array):
        # 显示指定的图片
        if isinstance(image_array, Image.Image):  # 如果是Pillow的Image对象
            image_array = np.array(image_array)  # 转换为NumPy数组

        if len(image_array.shape) == 3 and image_array.shape[2] == 3:  # 确保是RGB格式
            qimage = QImage(image_array.data, image_array.shape[1], image_array.shape[0], image_array.shape[1] * 3, QImage.Format_RGB888)
        else:
            raise ValueError("Unsupported image format for display.")

        pixmap = QPixmap.fromImage(qimage)
        self.scene.clear()
        self.scene.addPixmap(pixmap)

    def display_highlighted_image(self, image_array):
        # 显示高亮图片（均衡化后的图像）
        qimage = QImage(image_array.data, image_array.shape[1], image_array.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.highlight_scene.clear()
        self.highlight_scene.addPixmap(pixmap)

    def adjust_view_size(self):
        # 调整 QGraphicsView 的大小以适应图片
        if self.image is not None:
            max_width, max_height = 600, 600  # 窗口的最大宽高
            width, height = self.image.size

            # 如果图片超过窗口大小，则按比例缩放
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)  # 使用 LANCZOS 代替 ANTIALIAS
                self.image_array = np.array(self.image)  # 更新缩放后的数组
                self.image_hsv = self.rgb_to_hsv(self.image_array)  # 更新HSV数据

            self.graphics_view.setFixedSize(self.image.size[0] + 2, self.image.size[1] + 2)  # 加2以避免边框裁剪
            self.scene.setSceneRect(0, 0, self.image.size[0], self.image.size[1])

    def get_pixel_color(self, event):
        if self.image_hsv is not None:
            # 获取点击位置
            pos = self.graphics_view.mapToScene(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # 检查点击位置是否在图片范围内
            if 0 <= x < self.image_hsv.shape[1] and 0 <= y < self.image_hsv.shape[0]:
                self.selected_color_hsv = self.image_hsv[y, x]  # 获取选中的HSV颜色
                selected_color_rgb = self.image_array[y, x]  # 获取选中的RGB颜色
                color_hex = f"#{selected_color_rgb[0]:02x}{selected_color_rgb[1]:02x}{selected_color_rgb[2]:02x}"

                # 更新颜色标签
                self.color_label.setText(f"选中颜色: HSV{tuple(self.selected_color_hsv)}")
                self.color_label.setStyleSheet(f"background-color: {color_hex};")

                # 同步滑块位置到选中颜色，并设置范围为当前值正负10
                range_offset = 20  # 范围偏移量
                self.h_slider_min.setValue(max(0, self.selected_color_hsv[0] - range_offset))
                self.h_slider_max.setValue(min(255, self.selected_color_hsv[0] + range_offset))
                self.s_slider_min.setValue(max(0, self.selected_color_hsv[1] - range_offset))
                self.s_slider_max.setValue(min(255, self.selected_color_hsv[1] + range_offset))
                self.v_slider_min.setValue(max(0, self.selected_color_hsv[2] - range_offset))
                self.v_slider_max.setValue(min(255, self.selected_color_hsv[2] + range_offset))

                # 在选中位置显示颜色
                self.scene.clear()  # 清空场景
                self.display_image(self.image)  # 重新显示图片
                rect_size = 10  # 矩形大小
                rect = self.scene.addRect(
                    x - rect_size // 2, y - rect_size // 2, rect_size, rect_size,
                    pen=QPen(Qt.NoPen), brush=QBrush(QColor(*selected_color_rgb))  # 使用 QPen 和 QBrush
                )
                rect.setZValue(1)  # 确保矩形在图片之上

                # 重新计算高亮区域
                self.calculate_area()

    def calculate_area(self):
        if self.image_hsv is not None:
            try:
                # 根据滑块范围计算符合条件的像素
                mask = (
                    (self.h_range[0] <= self.image_hsv[:, :, 0]) & (self.image_hsv[:, :, 0] <= self.h_range[1]) &
                    (self.s_range[0] <= self.image_hsv[:, :, 1]) & (self.image_hsv[:, :, 1] <= self.s_range[1]) &
                    (self.v_range[0] <= self.image_hsv[:, :, 2]) & (self.image_hsv[:, :, 2] <= self.v_range[1])
                )

                # 高亮符合条件的像素
                highlighted_image = self.image_array.copy()
                highlighted_image[~mask] = [0, 0, 0]  # 将不符合条件的像素设为黑色
                highlighted_image = Image.fromarray(highlighted_image)
                highlight_qimage = QImage(highlighted_image.tobytes(), highlighted_image.width, highlighted_image.height, QImage.Format_RGB888)
                highlight_pixmap = QPixmap.fromImage(highlight_qimage)
                self.highlight_scene.clear()
                self.highlight_scene.addPixmap(highlight_pixmap)

                # 显示原始二值化图像在左下角
                binary_image = (mask * 255).astype(np.uint8)  # 将布尔值转换为二值化图像
                binary_qimage = QImage(binary_image.data, binary_image.shape[1], binary_image.shape[0], QImage.Format_Grayscale8)
                binary_pixmap = QPixmap.fromImage(binary_qimage)
                self.binary_scene.clear()
                self.binary_scene.addPixmap(binary_pixmap)

                # 对二值化图像进行开操作和闭操作
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))  # 椭圆形核
                opened_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)  # 开操作
                cleaned_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, kernel)  # 闭操作

                # 确保右下角图像为灰度图
                cleaned_image = cleaned_image.astype(np.uint8)

                # 提取曲线中心线
                centerline = self.extract_centerline(cleaned_image)

                # 在右下角图像中绘制中心线
                for y, x in enumerate(centerline):
                    if 0 <= x < cleaned_image.shape[1]:
                        cleaned_image[y, x] = 128  # 用灰色表示中心线

                # 显示处理后的图像
                cleaned_qimage = QImage(cleaned_image.data, cleaned_image.shape[1], cleaned_image.shape[0], QImage.Format_Grayscale8)
                cleaned_pixmap = QPixmap.fromImage(cleaned_qimage)
                if not hasattr(self, "cleaned_scene"):  # 如果右下角场景不存在，则创建
                    self.cleaned_scene = QGraphicsScene()
                    self.empty_view.setScene(self.cleaned_scene)
                self.cleaned_scene.clear()
                self.cleaned_scene.addPixmap(cleaned_pixmap)

                # 统计右下角图片中白色像素的数量
                white_pixel_count = np.sum(cleaned_image == 255)
                self.area_label.setText(f"符合条件的像素面积: {white_pixel_count}")
            except Exception as e:
                self.area_label.setText(f"错误: {str(e)}")

    def extract_centerline(self, binary_image):
        """
        提取二值化图像中曲线的中心线。
        """
        # 计算距离变换
        distance_transform = scipy.ndimage.distance_transform_edt(binary_image)

        # 找到距离变换的局部最大值（即中心线）
        centerline = np.argmax(distance_transform, axis=1)

        return centerline

    @staticmethod
    def rgb_to_hsv(image_array):
        # 使用OpenCV将RGB图像转换为HSV
        return cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

    def add_table(self):
        # 创建表格
        self.table = QTableWidget(3, 4)  # 3 行 4 列
        self.table.setHorizontalHeaderLabels(["总和", "颜色1", "颜色2", "颜色3"])
        self.table.setVerticalHeaderLabels(["颜色", "像素数量", "占比"])  # 调整行顺序
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.select_column)  # 绑定单元格点击事件
        self.layout.addWidget(self.table)

        # 初始化表格数据
        self.update_table()

    def select_column(self, row, column):
        # 记录用户选中的列
        if column > 0:  # 忽略第一列
            self.selected_column = column

    def update_table(self):
        # 更新表格数据
        total_pixels = self.image_array.shape[0] * self.image_array.shape[1] if self.image_array is not None else 1

        # 获取每种颜色的像素数量
        color1_pixels = int(self.table.item(1, 1).text()) if self.table.item(1, 1) else 0
        color2_pixels = int(self.table.item(1, 2).text()) if self.table.item(1, 2) else 0
        color3_pixels = int(self.table.item(1, 3).text()) if self.table.item(1, 3) else 0

        # 计算总和像素数量
        total_color_pixels = color1_pixels + color2_pixels + color3_pixels
        self.table.setItem(1, 0, QTableWidgetItem(str(total_color_pixels)))

        # 计算占比（基于三种颜色总和）
        self.table.setItem(2, 0, QTableWidgetItem("100%"))
        self.table.setItem(2, 1, QTableWidgetItem(f"{color1_pixels / total_color_pixels * 100:.2f}%" if total_color_pixels > 0 else "0%"))
        self.table.setItem(2, 2, QTableWidgetItem(f"{color2_pixels / total_color_pixels * 100:.2f}%" if total_color_pixels > 0 else "0%"))
        self.table.setItem(2, 3, QTableWidgetItem(f"{color3_pixels / total_color_pixels * 100:.2f}%" if total_color_pixels > 0 else "0%"))

    def set_gradient_color(self, row, col, range_values, channel=None):
        # 设置渐变颜色块
        gradient = QLinearGradient(0, 0, 1, 0)
        if channel == "H":
            gradient.setColorAt(0, QColor.fromHsv(range_values[0], 255, 255))
            gradient.setColorAt(1, QColor.fromHsv(range_values[1], 255, 255))
        elif channel == "S":
            gradient.setColorAt(0, QColor.fromHsv(0, range_values[0], 255))
            gradient.setColorAt(1, QColor.fromHsv(0, range_values[1], 255))
        elif channel == "V":
            gradient.setColorAt(0, QColor.fromHsv(0, 255, range_values[0]))
            gradient.setColorAt(1, QColor.fromHsv(0, 255, range_values[1]))

        brush = QBrush(gradient)
        item = QTableWidgetItem()
        item.setBackground(brush)
        self.table.setItem(row, col, item)

    def calculate_pixels_in_range(self, range_values, channel):
        if self.image_hsv is not None:
            mask = (range_values[0] <= self.image_hsv[:, :, channel]) & (range_values[1] <= self.image_hsv[:, :, channel])
            return np.sum(mask)
        return 0

    def add_save_buttons(self):
        # 创建水平布局
        save_buttons_layout = QHBoxLayout()

        # 保存颜色1按钮
        self.save_color1_button = QPushButton("保存颜色1")
        self.save_color1_button.clicked.connect(lambda: self.save_range_data(1))
        save_buttons_layout.addWidget(self.save_color1_button)

        # 保存颜色2按钮
        self.save_color2_button = QPushButton("保存颜色2")
        self.save_color2_button.clicked.connect(lambda: self.save_range_data(2))
        save_buttons_layout.addWidget(self.save_color2_button)

        # 保存颜色3按钮
        self.save_color3_button = QPushButton("保存颜色3")
        self.save_color3_button.clicked.connect(lambda: self.save_range_data(3))
        save_buttons_layout.addWidget(self.save_color3_button)

        # 将水平布局添加到主布局
        self.layout.addLayout(save_buttons_layout)

        # 添加输入框
        self.add_input_fields()

    def add_input_fields(self):
        # 创建水平布局
        input_layout = QHBoxLayout()

        # 微流芯片体积 V 输入框
        self.volume_label = QLabel("微流芯片体积:")
        self.volume_input = QLineEdit()
        input_layout.addWidget(self.volume_label)
        input_layout.addWidget(self.volume_input)

        # A液流速 v_A 输入框
        self.flow_a_label = QLabel("A液流速:")
        self.flow_a_input = QLineEdit()
        input_layout.addWidget(self.flow_a_label)
        input_layout.addWidget(self.flow_a_input)

        # B液流速 v_B 输入框
        self.flow_b_label = QLabel("B液流速:")
        self.flow_b_input = QLineEdit()
        input_layout.addWidget(self.flow_b_label)
        input_layout.addWidget(self.flow_b_input)

        # 将输入框布局添加到主布局
        self.layout.addLayout(input_layout)

    def save_range_data(self, column):
        # 保存当前滑块范围数据到指定列
        # 填写像素数量
        area_text = self.area_label.text()
        area_value = int(area_text.split(": ")[1])
        self.table.setItem(1, column, QTableWidgetItem(str(area_value)))

        # 设置单元格背景颜色为当前 HSV 范围的中间值
        mid_h = (self.h_range[0] + self.h_range[1]) // 2
        mid_s = (self.s_range[0] + self.s_range[1]) // 2
        mid_v = (self.v_range[0] + self.v_range[1]) // 2
        color = QColor.fromHsv(mid_h, mid_s, mid_v)
        item = QTableWidgetItem()
        item.setBackground(QBrush(color))
        self.table.setItem(0, column, item)

        # 更新表格数据
        self.update_table()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ColorExtractorApp()
    main_window.show()
    sys.exit(app.exec_())
