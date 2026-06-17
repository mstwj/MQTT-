from machine import UART
import utime

# 初始化串口：HaaS506 485 对应 UART2
uart = UART(2, 9600, bits=8, parity=None, stop=1, timeout=1000)

# CRC16 校验
def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

# 读保持寄存器 H03
def H03(addr, reg, length=1):
    try:
        uart.read()  # 清空缓存
        cmd = bytearray([addr, 3, (reg >> 8) & 0xFF, reg & 0xFF, 0, length])
        cmd += crc16(cmd)
        uart.write(cmd)
        utime.sleep(0.3)
        
        res = uart.read()
        if res and len(res) >= 5 + 2 * length:
            values = []
            for i in range(length):
                val = (res[3 + i*2] << 8) | res[4 + i*2]
                values.append(val)
            return values
    except:
        pass
    return None