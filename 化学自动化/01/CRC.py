def crc16(data: bytes) -> bytes:  
    """  
    计算 CRC-16 (Modbus) 校验码  
    :param data: 输入数据字节流  
    :return: CRC 校验码（2字节）  
    """    
    crc = 0xFFFF  
    for byte in data:  
        crc ^= byte  
        for _ in range(8):  
            if crc & 0x0001:  
                crc = (crc >> 1) ^ 0xA001  
            else:  
                crc >>= 1  
    # 返回 CRC 的低字节和高字节  
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])  
  
  
def hex_string_to_bytes(hex_string: str) -> bytes:  
    """  
    将十六进制字符串（每个数字用空格隔开）转换为字节流  
    :param hex_string: 十六进制字符串，例如 "01 06 00 06 00 0A"    :return: 字节流  
    """    # 去除空格并按每两个字符分组  
    hex_values = hex_string.replace(" ", "")  
    # 将每两个字符转换为一个字节  
    return bytes.fromhex(hex_values)  
  
  
if __name__ == "__main__":  
    # 示例输入：十六进制字符串，每个数字用空格隔开  
    hex_input = input()  
  
    # 将字符串转换为字节流  
    data_frame = hex_string_to_bytes(hex_input)  
  
    # 计算 CRC 校验码  
    crc = crc16(data_frame)  
  
    # 组合完整帧  
    complete_frame = data_frame + crc  
  
    print("原始数据帧（十六进制）:", data_frame.hex())  
    print("CRC 校验码（十六进制）:", crc.hex())  
    print("完整数据帧（十六进制）:", complete_frame.hex())