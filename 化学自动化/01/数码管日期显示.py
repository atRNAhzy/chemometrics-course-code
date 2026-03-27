from datetime import datetime
import time
import serial

# 获取当前时间日期并格式化
def get_current_date_time():
    # 获取当前日期和时间
    now = datetime.now()
    
    # 格式化日期为 "MM-DD"
    date_str = now.strftime("%m-%d")
    
    # 格式化时间为 "HH.MM"
    time_str = now.strftime("%H.%M")
    
    return date_str, time_str

# 配置串口参数，请根据实际情况修改
PORT = "/dev/ttyUSB0" # 串口号，根据实际情况修改
BAUDRATE = 9600  # 波特率
PARITY = 'N'  # 校验位
STOPBITS = 1  # 停止位
BYTESIZE = 8  # 数据位

# 初始化串口
try:
    ser = serial.Serial(PORT, BAUDRATE, parity=PARITY, stopbits=STOPBITS, bytesize=BYTESIZE, timeout=0.1)
    if ser.is_open:
        print(f"串口 {PORT} 已打开")
except Exception as e:
    print(f"串口打开失败: {e}")
    exit()

# 将字符串显示在数码管显示屏上
def show_on_screen(address, content):
    """
    将字符串显示在数码管显示屏上
    :param address: 屏的地址码（字符串，如 "001"）
    :param content: 要显示的内容（字符串）
    """
    if not ser.is_open:
        print("串口未打开")
        return
    
    # 构造命令
    command = f"${address},{content}#"
    
    try:
        # 发送命令
        ser.write(command.encode('utf-8'))
        print(f"发送命令: {command}")
    except Exception as e:
        print(f"发送命令失败: {e}")

# 示例 usage
if __name__ == "__main__":

    # 示例调用
    while True:
        date,time1 = get_current_date_time()
        show_on_screen("001",date)
        time.sleep(2)
        show_on_screen("001",time1)
        time.sleep(2)






