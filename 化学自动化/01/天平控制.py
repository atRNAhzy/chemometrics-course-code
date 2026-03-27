import serial

class BalanceController:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        初始化天平控制器
        :param port: 串口号（如 'COM1' 或 '/dev/ttyUSB0'）
        :param baudrate: 波特率，默认 9600
        :param timeout: 超时时间，默认 1 秒
        """
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=timeout
        )

    def send_command(self, command):
        """
        发送指令到天平
        :param command: 指令字符串
        :return: 天平的响应
        """
        self.ser.write((command + '\r\n').encode('utf-8'))  # 发送指令
        response = self.ser.read_all().decode('utf-8')      # 读取响应
        return response.strip()

    def tare(self):
        """
        清零（去皮）
        :return: 天平的响应
        """
        return self.send_command('Z')

    def get_stable_weight(self):
        """
        获取稳定的称量值
        :return: 称量值（字符串，格式需要根据实际设备调试）
        """
        return self.send_command('S')

    def close(self):
        """
        关闭串口连接
        """
        self.ser.close()
# 示例用法
if __name__ == "__main__":
    # 初始化控制器
    balance = BalanceController(port='COM3')  # 修改为实际串口号

    try:
        # 清零（去皮）
        tare_response = balance.tare()
        print(f"清零响应: {tare_response}")

        # 获取稳定的称量值
        weight = balance.get_stable_weight()
        print(f"稳定称量值: {weight}")

    finally:
        # 关闭连接
        balance.close()