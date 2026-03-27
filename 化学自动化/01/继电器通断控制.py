import serial
import time

# 配置串口
ser = serial.Serial(
    port='/dev/ttyUSB0',  # 修改为实际串口号
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

# 发送指令并接收返回
def send_command(command_hex):
    command_bytes = bytes.fromhex(command_hex)
    ser.write(command_bytes)
    time.sleep(0.1)  # 等待设备响应
    response = ser.read_all()
    print(f"发送命令: {command_hex}, 接收响应: {response.hex()}")
    #decode_relay_status(response)
    return response.hex()

# 打开1号继电器（手动模式）
def open_relay_1():
    command = "FF 05 00 00 FF 00 99 E4"
    response = send_command(command)
    print(f"打开1号继电器（手动模式）: 发送 {command}, 返回 {response}")

# 关闭1号继电器（手动模式）
def close_relay_1():
    command = "FF 05 00 00 00 00 D8 14"
    response = send_command(command)
    print(f"关闭1号继电器（手动模式）: 发送 {command}, 返回 {response}")

# 打开所有继电器
def open_all_relays():
    command = "FF 0F 00 00 00 08 01 FF 30 1D"
    response = send_command(command)
    print(f"打开所有继电器: 发送 {command}, 返回 {response}")

# 关闭所有继电器
def close_all_relays():
    command = "FF 0F 00 00 00 08 01 00 70 5D"
    response = send_command(command)
    print(f"关闭所有继电器: 发送 {command}, 返回 {response}")

# 解读读取继电器状态的返回值
def decode_relay_status(response_bytes):
    """
    解读读取继电器状态的返回值，并按照指定格式返回。

    参数:
        response_bytes (bytes): 返回的字节流，例如 b'\xFF\x01\x01\x01\xA1\xA0'。

    返回:
        str: 继电器状态字符串，格式为 "继电器状态： 关 关 关 关 关 关 关 关"。
    """
    # 将字节流转换为十六进制字符串
    response_hex = response_bytes.hex().upper()

    # 检查返回值长度
    if len(response_hex) == 0:
        print("未接收到响应数据")
        return

    if len(response_hex) != 10:
        raise ValueError("返回值长度不正确，应为 10 个字符（5 字节）。")

    # 提取数据部分（第 4 字节）
    data_byte = response_hex[6:8]  # 第 4 字节
    data_int = int(data_byte, 16)  # 转换为整数

    # 解析每个继电器的状态
    status_list = []
    for i in range(8):  # 8 个继电器
        state = (data_int >> i) & 0x01  # 获取第 i 位的值
        status_list.append("开" if state else "关")

    # 按照指定格式返回
    print(f"继电器状态： {' '.join(status_list)}")

# 主程序
if __name__ == "__main__":

    while 1:
    
        # 示例操作
        open_relay_1()
        time.sleep(2)

        close_relay_1()
        time.sleep(2)

        open_all_relays()
        time.sleep(2)

        close_all_relays()
        time.sleep(2)


