import serial
import time
from 注射泵控制 import SyringePumpController

import time



def send_hex_command(port, baudrate, hex_command):
    """
    通过串口发送 16 进制指令，并接收返回的响应。

    参数:
        port (str): 串口号，例如 '/dev/ttyUSB0' 或 'COM3'。
        baudrate (int): 波特率，例如 9600。
        hex_command (str): 16 进制指令字符串，例如 "FF 05 00 00 FF 00 99 E4"。
    """
    try:
        # 初始化串口
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )

        if ser.is_open:
            print(f"串口 {port} 已打开")

        # 将 16 进制指令转换为字节流
        command_bytes = bytes.fromhex(hex_command.replace(" ", ""))
        print(command_bytes)
    

        # 发送指令
        ser.write(command_bytes)
        print(f"发送指令: {hex_command}")

        # 等待设备响应
        time.sleep(0.1)  # 根据设备响应时间调整
        response = ser.read_all()

        # 打印响应
        if response:
            print(f"接收响应: {response.hex().upper()}")
        else:
            print("未接收到响应数据")

    except Exception as e:
        print(f"串口通信失败: {e}")
    finally:
        if ser.is_open:
            ser.close()
            print(f"串口 {port} 已关闭")


class SyringePumpController:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        初始化注射泵控制器
        :param port: 串口号（如 'COM3' 或 '/dev/ttyUSB0'）
        :param baudrate: 波特率，默认为 9600
        :param timeout: 超时时间，默认为 1 秒
        """
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=timeout
        )
    
    def _send_command(self, hex_str):
        """
        发送十六进制指令并返回响应
        :param hex_str: 十六进制字符串（如 "01 06 00 00 00 01 48 0A"）
        :return: 设备返回的响应数据
        """
        data = bytes.fromhex(hex_str.replace(" ", ""))
        self.ser.write(data)
        print(f'发送：{data}')
        return self.ser.read_all()
    
    def _calculate_crc(self, data_hex):
        """
        计算CRC校验码
        :param data_hex: 十六进制字符串（如 "01 06 00 00 00 01"）
        :return: CRC校验码（2字节）
        """
        data_bytes = bytes.fromhex(data_hex.replace(" ", ""))
        crc = 0xFFFF
        for byte in data_bytes:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    
    def _build_command(self, addr, func_code, reg_addr, data):
        """
        构建完整指令
        :param addr: 设备地址（如 0x0A）
        :param func_code: 功能码（如 0x06）
        :param reg_addr: 寄存器地址（如 0x0005）
        :param data: 数据（如 0x00FF）
        :return: 完整的十六进制指令字符串
        """
        # 构建基础指令
        base_cmd = f"{addr:02X}{func_code:02X}{reg_addr >> 8:02X}{reg_addr & 0xFF:02X}{data >> 8:02X}{data & 0xFF:02X}"
        
        # 计算CRC
        crc = self._calculate_crc(base_cmd)
        # 将CRC附加到指令末尾
        full_cmd = base_cmd + crc.hex().upper()
        print(f'构建指令：{full_cmd}')
        return full_cmd

    def set_speed(self, speed):
        """
        设置速度
        :param speed: 速度值（范围取决于设备，通常为0-255）
        """
        cmd = self._build_command(0x0A, 0x06, 0x0005, speed)
        self._send_command(cmd)
        print(f"速度设置为: {speed}")

    def set_pulse_count(self, pulse_count):
        """
        设置脉冲数
        :param pulse_count: 脉冲数（范围取决于设备，通常为0-65535）
        """
        cmd = self._build_command(0x0A, 0x06, 0x0007, pulse_count)
        self._send_command(cmd)
        print(f"脉冲数设置为: {pulse_count}")

    def forward(self):
        """
        正转
        """
        cmd = self._build_command(0x0A, 0x06, 0x0000, 0x0001)
        self._send_command(cmd)
        print("正转启动")

    def reverse(self):
        """
        反转
        """
        cmd = self._build_command(0x0A, 0x06, 0x0001, 0x0001)
        self._send_command(cmd)
        print("反转启动")

# 使用示例
if __name__ == "__main__":
    # 配置串口参数
    port = "/dev/ttyUSB0"  # 修改为实际串口号
    baudrate = 9600


    pump = SyringePumpController(port='/dev/ttyUSB0')  # 修改为实际串口号
    
    # 设置速度为100
    pump.set_speed(1000)
    
    # 设置脉冲数为500
    pump.set_pulse_count(20000)
    

    # 等待5秒
    time.sleep(5)
    
    # # 启动反转
    # pump.reverse()

