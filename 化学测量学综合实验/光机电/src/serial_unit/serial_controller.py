"""
串口控制器：封装串口通信逻辑
"""

from PyQt5 import QtCore
from typing import List
import os
from .command_parser import CommandParser
from .motor_commands import MotorCommands

# 串口依赖（可选）
try:
    import serial
    import serial.tools.list_ports as list_ports
except ImportError:
    serial = None
    list_ports = None

class SerialController(QtCore.QObject):
    """串口控制器类"""
    
    # 信号定义
    data_received = QtCore.pyqtSignal(dict)  # 接收到数据
    connection_changed = QtCore.pyqtSignal(bool, str)  # 连接状态变化 (connected, status_text)
    log_message = QtCore.pyqtSignal(str)  # 日志消息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 串口相关
        self.serial_port = None
        self.is_simulation_mode = False
        
        # 解析器
        self.parser = CommandParser()
        self.commands = MotorCommands()
        
        # 定时器用于轮询串口数据
        self.poll_timer = QtCore.QTimer(self)
        self.poll_timer.setInterval(50)  # 50ms轮询间隔
        self.poll_timer.timeout.connect(self._poll_serial_data)
        
        # 记录最后的电机速度（用于兼容模式）
        self.last_motor1_speed = 0
        self.last_motor2_speed = 0
        # 模拟数据相关
        self._sim_lines = []
        self._sim_index = 0
        self._sim_running = False

    def start_simulation(self, reset: bool = True):
        """开始/恢复模拟数据播放。reset=True 时从头开始播放。"""
        if reset:
            self._sim_index = 0
        self._sim_running = True
        self.log_message.emit("模拟数据播放已启动")

    def stop_simulation(self):
        """暂停模拟数据播放，但保留当前索引。"""
        self._sim_running = False
        self.log_message.emit("模拟数据播放已暂停")
    
    def get_available_ports(self) -> List[str]:
        """获取可用串口列表"""
        ports = ["模拟数据"]  # 始终包含模拟数据选项
        
        if list_ports is None:
            ports.append("未安装pyserial")
            return ports
            
        try:
            serial_ports = list(list_ports.comports())
            for port in serial_ports:
                ports.append(port.device)
        except Exception:
            pass
            
        if len(ports) == 1:  # 只有模拟数据选项
            ports.append("无可用端口")
            
        return ports
    
    def connect_port(self, port_name: str) -> bool:
        """
        连接到指定端口
        
        Args:
            port_name: 端口名称，可以是"模拟数据"或实际串口名
            
        Returns:
            bool: 连接是否成功
        """
        # 先断开现有连接
        self.disconnect_port()
        
        if port_name == "模拟数据":
            self.is_simulation_mode = True
            # 初始化模拟数据文件（优先使用 workspace 下的 results/raw/wtf-4-!!!.txt）
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                sim_path = os.path.join(base_dir, 'results', 'raw', 'wtf-4-!!!.txt')
                if os.path.exists(sim_path):
                    with open(sim_path, 'r', encoding='utf-8') as f:
                        lines = f.read().splitlines()
                    # 跳过表头并过滤空行
                    self._sim_lines = [l for l in lines[1:] if l.strip()]
                    self._sim_index = 0
                    self.log_message.emit(f"已加载模拟数据：{sim_path} （{len(self._sim_lines)} 行）")
                else:
                    self._sim_lines = []
                    self._sim_index = 0
                    self.log_message.emit(f"未找到模拟数据文件: {sim_path}，将发送空数据")
            except Exception as e:
                self._sim_lines = []
                self._sim_index = 0
                self.log_message.emit(f"加载模拟数据失败: {e}")

            self.poll_timer.start()
            self.connection_changed.emit(True, "模拟数据模式")
            self.log_message.emit("已切换到模拟数据模式")
            return True
            
        # 连接真实串口
        if serial is None:
            self.log_message.emit("请先安装 pyserial: pip install pyserial")
            return False
            
        if not port_name or port_name.startswith(("无可用", "未安装")):
            self.log_message.emit("没有可用串口")
            return False
            
        try:
            self.serial_port = serial.Serial(port=port_name, baudrate=115200, timeout=0)
            self.is_simulation_mode = False
            self.poll_timer.start()
            self.connection_changed.emit(True, f"已连接 {port_name}")
            return True
        except Exception as e:
            self.log_message.emit(f"连接失败: {e}")
            return False
    
    def disconnect_port(self):
        """断开串口连接"""
        try:
            self.poll_timer.stop()
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.serial_port = None
        except Exception:
            pass
            
        self.is_simulation_mode = False
        self.connection_changed.emit(False, "未连接")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        if self.is_simulation_mode:
            return True
        return self.serial_port is not None and self.serial_port.is_open
    
    def send_command(self, command: str) -> bool:
        """
        发送命令到串口
        
        Args:
            command: 要发送的命令字符串
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected():
            self.log_message.emit("未连接串口")
            return False
            
        try:
            if self.is_simulation_mode:
                # 模拟模式：只记录命令
                formatted_cmd = self.commands.format_command_log(command)
                self.log_message.emit(f"模拟模式: {formatted_cmd}")
            else:
                # 真实串口：发送命令
                self.serial_port.write((command + "\n").encode('utf-8'))
                formatted_cmd = self.commands.format_command_log(command)
                self.log_message.emit(formatted_cmd)
            return True
        except Exception as e:
            self.log_message.emit(f"发送失败: {e}")
            return False
    
    def _poll_serial_data(self):
        """轮询串口数据。在模拟模式下，从预加载文件逐行返回数据点。"""
        if self.is_simulation_mode:
            # 如果未启动播放，则直接返回（仍然维持连接状态）
            if not getattr(self, '_sim_running', False):
                return

            # 从 _sim_lines 中按序取行并发送数据
            try:
                if self._sim_index >= len(self._sim_lines):
                    # 到达文件末尾，停止播放并通知（发送 titration_stop 类型）
                    try:
                        self._sim_running = False
                    except Exception:
                        pass
                    # 发送结束信号到上层（与现有协议保持一致）
                    self.data_received.emit({'type': 'titration_stop'})
                    self.log_message.emit('模拟数据已播放完毕')
                    return

                line = self._sim_lines[self._sim_index]
                self._sim_index += 1
                parts = [p.strip() for p in line.split(',')]
                # 期望格式：time_s,conductivity,motor1_proportion
                if len(parts) >= 3:
                    try:
                        # 解析数值
                        time_s = float(parts[0])
                        conductivity = float(parts[1])
                        proportion = float(parts[2])
                    except Exception:
                        # 跳过解析失败的行
                        return

                    # 将 proportion 转换为 motor1 speed（使用父控件的 max_speed_input 值作为参考）
                    motor1_speed = 0
                    motor2_speed = 0
                    try:
                        parent = self.parent()
                        if parent and hasattr(parent, 'ui') and hasattr(parent.ui, 'max_speed_input'):
                            max_sp = int(parent.ui.max_speed_input.value())
                            motor1_speed = int(round(proportion * max_sp))
                        else:
                            motor1_speed = int(round(proportion * 10000))
                    except Exception:
                        motor1_speed = int(round(proportion * 10000))

                    # 发送数据字典，格式与真实串口解析一致
                    self.data_received.emit({
                        'motor1': motor1_speed,
                        'motor2': motor2_speed,
                        'conductivity': conductivity
                    })
                return
            except Exception as e:
                self.log_message.emit(f"模拟数据轮询错误: {e}")
                return
            
        if not (self.serial_port and self.serial_port.is_open):
            return
            
        try:
            bytes_available = self.serial_port.in_waiting
            if bytes_available == 0:
                return
                
            data = self.serial_port.read(bytes_available)
            text = data.decode(errors='ignore')
            
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                    
                self.log_message.emit(f"Arduino: {line}")
                
                # 解析数据
                parsed = self.parser.parse_arduino_data(line)
                if parsed:
                    self._handle_parsed_data(parsed)
                    
        except Exception as e:
            self.log_message.emit(f"串口读取错误: {e}")
    
    def _handle_parsed_data(self, parsed_data: dict):
        """处理解析后的数据"""
        data_type = parsed_data.get('type')
        
        if data_type == 'data':
            # 完整数据：包含电机速度和电导率
            motor1 = parsed_data['motor1']
            motor2 = parsed_data['motor2']
            conductivity = parsed_data['conductivity']
            
            self.last_motor1_speed = motor1
            self.last_motor2_speed = motor2
            
            self.log_message.emit(f"m1={motor1}, m2={motor2}, EC={conductivity:.3f}")
            self.data_received.emit({
                'motor1': motor1,
                'motor2': motor2, 
                'conductivity': conductivity
            })
            
        elif data_type == 'conductivity_only':
            # 仅电导率数据，使用上次的电机速度
            conductivity = parsed_data['conductivity']
            self.log_message.emit(f"COND: {conductivity:.3f}")
            self.data_received.emit({
                'motor1': self.last_motor1_speed,
                'motor2': self.last_motor2_speed,
                'conductivity': conductivity
            })
            
        elif data_type == 'motors_only':
            # 仅电机速度数据
            motor1 = parsed_data['motor1']
            motor2 = parsed_data['motor2']
            self.last_motor1_speed = motor1
            self.last_motor2_speed = motor2
            
            # 如果同时包含电导率，则发送完整数据
            if 'conductivity' in parsed_data:
                conductivity = parsed_data['conductivity']
                self.log_message.emit(f"COND: {conductivity:.3f}")
                self.data_received.emit({
                    'motor1': motor1,
                    'motor2': motor2,
                    'conductivity': conductivity
                })
                
        elif data_type == 'legacy_data':
            # 兼容格式的完整数据
            motor1 = parsed_data['motor1']
            motor2 = parsed_data['motor2']
            conductivity = parsed_data['conductivity']
            
            self.last_motor1_speed = motor1
            self.last_motor2_speed = motor2
            
            self.log_message.emit(f"COND: {conductivity:.3f}")
            self.data_received.emit({
                'motor1': motor1,
                'motor2': motor2,
                'conductivity': conductivity
            })
            
        elif data_type == 'stop':
            # 滴定结束信号
            self.data_received.emit({'type': 'titration_stop'})
    
    # 电机控制便捷方法
    def motor_forward(self, motor_id: int, speed: int) -> bool:
        """电机正转"""
        cmd = self.commands.motor_forward(motor_id, speed)
        return self.send_command(cmd)
    
    def motor_backward(self, motor_id: int, speed: int) -> bool:
        """电机反转"""
        cmd = self.commands.motor_backward(motor_id, speed)
        return self.send_command(cmd)
    
    def motor_stop(self, motor_id: int) -> bool:
        """停止电机"""
        cmd = self.commands.motor_stop(motor_id)
        return self.send_command(cmd)
    
    def start_titration(self, max_speed: int, increment_ms: int) -> bool:
        """开始滴定"""
        cmd = self.commands.start_titration(max_speed, increment_ms)
        return self.send_command(cmd)
    
    def emergency_stop(self) -> bool:
        """紧急停止"""
        cmd = self.commands.emergency_stop()
        return self.send_command(cmd)