import serial
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

# 示例用法
if __name__ == "__main__":
    # 配置串口参数
    port = "/dev/ttyUSB0"  # 修改为实际串口号
    baudrate = 9600

    # 输入 16 进制指

    # 发送指令

    for i in range(5):
        send_hex_command(port, baudrate, "0A 06 00 01 00 01 18 B1") 
        #send_hex_command(port, baudrate, "0A 06 00 00 00 01 49 71")
        time.sleep(10)