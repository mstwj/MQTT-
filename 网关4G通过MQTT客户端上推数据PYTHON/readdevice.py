import network
import utime as time
import machine
from machine import UART, Pin
import time

import json

time.sleep_ms(1000)
Pin(39, Pin.IN, pull=None)
time.sleep_ms(50)

TX = 37
RX = 39
DE = 38        

uart = UART(2, 9600, tx=TX, rx=RX, timeout=1000)
de = Pin(DE, Pin.OUT)

de.value(0)
uart.read()



reg_name_map = {
    69:{"name":"Ua","scale":10,"unit":"V"},
    70:{"name":"Ia","scale":10,"unit":"A"},
    71:{"name":"Cabinet_Current_A","scale":10,"unit":"A"},
    72:{"name":"Sys_Freq_Ua","scale":10,"unit":"Hz"},
    73:{"name":"Phase_A_Active_Power","scale":10,"unit":"kW"},      
}

'''
reg_name_map = {
    
    # 三相电参 69~104
    69:{"name":"Ua","scale":10,"unit":"V"},
    70:{"name":"Ia","scale":10,"unit":"A"},
    71:{"name":"Cabinet_Current_A","scale":10,"unit":"A"},
    72:{"name":"Sys_Freq_Ua","scale":10,"unit":"Hz"},
    73:{"name":"Phase_A_Active_Power","scale":10,"unit":"kW"},    
    
    # 模组容量 0~31
 
    0:{"name":"第1台模组容量","scale":10,"unit":"kVar"},    
    1:{"name":"第2台模组容量","scale":10,"unit":"kVar"},
    2:{"name":"第3台模组容量","scale":10,"unit":"kVar"},
    3:{"name":"第4台模组容量","scale":10,"unit":"kVar"},
    4:{"name":"第5台模组容量","scale":10,"unit":"kVar"},
    5:{"name":"第6台模组容量","scale":10,"unit":"kVar"},
    6:{"name":"第7台模组容量","scale":10,"unit":"kVar"},
    7:{"name":"第8台模组容量","scale":10,"unit":"kVar"},
    8:{"name":"第9台模组容量","scale":10,"unit":"kVar"},
    9:{"name":"第10台模组容量","scale":10,"unit":"kVar"},
    10:{"name":"第11台模组容量","scale":10,"unit":"kVar"},
    11:{"name":"第12台模组容量","scale":10,"unit":"kVar"},
    12:{"name":"第13台模组容量","scale":10,"unit":"kVar"},
    13:{"name":"第14台模组容量","scale":10,"unit":"kVar"},
    14:{"name":"第15台模组容量","scale":10,"unit":"kVar"},
    15:{"name":"第16台模组容量","scale":10,"unit":"kVar"},
    16:{"name":"第17台模组容量","scale":10,"unit":"kVar"},
    17:{"name":"第18台模组容量","scale":10,"unit":"kVar"},
    18:{"name":"第19台模组容量","scale":10,"unit":"kVar"},
    19:{"name":"第20台模组容量","scale":10,"unit":"kVar"},
    20:{"name":"第21台模组容量","scale":10,"unit":"kVar"},
    21:{"name":"第22台模组容量","scale":10,"unit":"kVar"},
    22:{"name":"第23台模组容量","scale":10,"unit":"kVar"},
    23:{"name":"第24台模组容量","scale":10,"unit":"kVar"},
    24:{"name":"第25台模组容量","scale":10,"unit":"kVar"},
    25:{"name":"第26台模组容量","scale":10,"unit":"kVar"},
    26:{"name":"第27台模组容量","scale":10,"unit":"kVar"},
    27:{"name":"第28台模组容量","scale":10,"unit":"kVar"},
    28:{"name":"第29台模组容量","scale":10,"unit":"kVar"},
    29:{"name":"第30台模组容量","scale":10,"unit":"kVar"},
    30:{"name":"第31台模组容量","scale":10,"unit":"kVar"},
    31:{"name":"第32台模组容量","scale":10,"unit":"kVar"},
    
    # 控制参数 36~65
    36:{"name":"投切方式","scale":1,"unit":"0手动/1自动"},
    37:{"name":"投切策略","scale":1,"unit":"0最优/1循环/2顺序"},
    38:{"name":"投入功率因数","scale":100,"unit":"cosφ"},
    39:{"name":"切除功率因数","scale":100,"unit":"cosφ"},
    40:{"name":"系统电流变比","scale":1,"unit":"倍"},
    41:{"name":"柜体电流变比","scale":1,"unit":"倍"},
    42:{"name":"投入检测延时","scale":1,"unit":"ms"},
    43:{"name":"切除检测延时","scale":1,"unit":"ms"},
    44:{"name":"投切间隔","scale":1,"unit":"ms"},
    45:{"name":"放电延时","scale":10,"unit":"ms"},
    46:{"name":"投入容量系数","scale":100,"unit":"倍数"},
    47:{"name":"切除容量系数","scale":100,"unit":"倍数"},
    48:{"name":"供电公司编码","scale":1,"unit":"ID"},
    49:{"name":"保护切除延时","scale":1,"unit":"ms"},
    50:{"name":"保护检测延时","scale":1,"unit":"ms"},
    51:{"name":"电压过压值","scale":1,"unit":"V"},
    52:{"name":"电压欠压值","scale":1,"unit":"V"},
    53:{"name":"THDU上限值(%)","scale":1,"unit":"%"},
    54:{"name":"THDI上限值(%)","scale":1,"unit":"%"},
    62:{"name":"柜体风机启动温度","scale":1,"unit":"℃"},
    63:{"name":"柜体THDI上限值(%)","scale":1,"unit":"%"},
    64:{"name":"投切参考条件","scale":1,"unit":"0次数/1时间"},
    65:{"name":"终端设备编码","scale":1,"unit":"ID"},

    # 三相电参 69~104
    69:{"name":"系统Ua电压","scale":10,"unit":"V"},
    70:{"name":"系统Ia电流","scale":10,"unit":"A"},
    71:{"name":"柜体A相电流","scale":10,"unit":"A"},
    72:{"name":"系统Ua频率","scale":10,"unit":"Hz"},
    73:{"name":"A相有功功率","scale":10,"unit":"kW"},
    74:{"name":"A相无功功率","scale":10,"unit":"kVar"},
    75:{"name":"A相视在功率","scale":10,"unit":"kVA"},
    76:{"name":"A相功率因数","scale":100,"unit":"cosφ"},
    77:{"name":"A相电压THD","scale":10,"unit":"%"},
    78:{"name":"A相电流THD","scale":10,"unit":"%"},

    79:{"name":"系统Ub电压","scale":10,"unit":"V"},
    80:{"name":"系统Ib电流","scale":10,"unit":"A"},
    81:{"name":"柜体B相电流","scale":10,"unit":"A"},
    82:{"name":"系统Ub频率","scale":10,"unit":"Hz"},
    83:{"name":"B相有功功率","scale":10,"unit":"kW"},
    84:{"name":"B相无功功率","scale":10,"unit":"kVar"},
    85:{"name":"B相视在功率","scale":10,"unit":"kVA"},
    86:{"name":"B相功率因数","scale":100,"unit":"cosφ"},
    87:{"name":"B相电压THD","scale":10,"unit":"%"},
    88:{"name":"B相电流THD","scale":10,"unit":"%"},

    89:{"name":"系统Uc电压","scale":10,"unit":"V"},
    90:{"name":"系统Ic电流","scale":10,"unit":"A"},
    91:{"name":"柜体C相电流","scale":10,"unit":"A"},
    92:{"name":"系统Uc频率","scale":10,"unit":"Hz"},
    93:{"name":"C相有功功率","scale":10,"unit":"kW"},
    94:{"name":"C相无功功率","scale":10,"unit":"kVar"},
    95:{"name":"C相视在功率","scale":10,"unit":"kVA"},
    96:{"name":"C相功率因数","scale":100,"unit":"cosφ"},
    97:{"name":"C相电压THD","scale":10,"unit":"%"},
    98:{"name":"C相电流THD","scale":10,"unit":"%"},

    99:{"name":"系统三相有功功率","scale":10,"unit":"kW"},
    100:{"name":"系统三相无功功率","scale":10,"unit":"kVar"},
    101:{"name":"系统三相视在功率","scale":10,"unit":"kVA"},
    102:{"name":"总功率因数","scale":100,"unit":"cosφ"},
    103:{"name":"总谐波电压畸变率","scale":10,"unit":"%"},
    104:{"name":"总谐波电流畸变率","scale":10,"unit":"%"},

    # 设备状态 105、109、110、111
    105:{"name":"运行状态","scale":1,"unit":"状态码"},
    109:{"name":"柜体温度","scale":10,"unit":"℃"},
    110:{"name":"开入量状态","scale":1,"unit":"位标志"},
    111:{"name":"开出量状态","scale":1,"unit":"位标志"},
    
}
'''

def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

# 解析单段应答数据，返回寄存器字典
def parse_modbus_resp(resp_data, reg_start, reg_cnt):
    res = {}
    if len(resp_data) < 5:
        return None
    slave = resp_data[0]
    func = resp_data[1]
    data_len = resp_data[2]
    data_buf = resp_data[3:-2]
    recv_crc = resp_data[-2:]
    calc_crc = crc16(resp_data[:-2])
    if recv_crc != calc_crc:
        print("CRC校验失败")
        return None
    if len(data_buf) != reg_cnt * 2:
        print("数据长度不匹配")
        return None
    # 循环拆分每一个寄存器
    for i in range(reg_cnt):
        offset = i * 2
        val_high = data_buf[offset]
        val_low = data_buf[offset + 1]
        reg_val = (val_high << 8) | val_low
        reg_addr = reg_start + i
        res[reg_addr] = reg_val
    return res



def read_meter(start_address,register_count):    
    # --------------------------
    # 这里是您需要修改的参数
    # --------------------------
    slave_address = 0x02       # 从机地址
    function_code = 0x03       # 功能码 (03=读保持寄存器)
    #start_address = 0x0045     # 起始寄存器地址 (十进制69)
    #register_count = 50        # 要读取的寄存器数量 (50个)
    # --------------------------
    # 参数修改结束
    # --------------------------

    # 构建Modbus指令的前6个字节
    cmd_body = bytearray([
        slave_address,
        function_code,
        (start_address >> 8) & 0xFF,  # 起始地址高8位
        start_address & 0xFF,         # 起始地址低8位
        (register_count >> 8) & 0xFF, # 寄存器数量高8位
        register_count & 0xFF          # 寄存器数量低8位
    ])

    # 计算并追加CRC校验码
    crc = crc16(cmd_body)
    cmd = cmd_body + crc

    print("发送：", cmd.hex())
    
    de.value(1)
    time.sleep_ms(2)
    uart.write(cmd)
    
    uart.flush() 
    de.value(0)
    time.sleep_ms(300)  # 增加延时，确保接收完所有数据
    data = uart.read()
    
    if data:
        print("接收：", data.hex())
        # 解析寄存器
        reg_dict = parse_modbus_resp(data, start_address, register_count)
        
        if reg_dict is None:
            return None

        # 提取A/B/C相关键数据（对照点表）
        #data = {}
        # A相 reg69~78
        #data["A相电压"] = reg_dict[69] / 10
        #data["A相电流"] = reg_dict[70] / 10
        #data["A相有功kW"] = reg_dict[73] / 10#
        #data["A相无功kVar"] = reg_dict[74] / 10
        #data["A相功率因数"] = reg_dict[76] / 100

        # B相 reg79~88
        #data["B相电压"] = reg_dict[79] / 10
        #data["B相电流"] = reg_dict[80] / 10
        #data["B相有功kW"] = reg_dict[83] / 10
        #data["B相无功kVar"] = reg_dict[84] / 10
        #data["B相功率因数"] = reg_dict[86] / 100

        # C相 reg89~98
        #data["C相电压"] = reg_dict[89] / 10
        #data["C相电流"] = reg_dict[90] / 10
        #data["C相有功kW"] = reg_dict[93] / 10
        #data["C相无功kVar"] = reg_dict[94] / 10
        #data["C相功率因数"] = reg_dict[96] / 100

        # 三相总参
        #data["总有功kW"] = reg_dict[99] / 10
        #data["总无功kVar"] = reg_dict[100] / 10
        #data["总功率因数"] = reg_dict[102] / 100
        #data["柜体温度"] = reg_dict[106] / 10

        #print("===== 三相解析结果 =====")
        #for k, v in data.items():
            #print(f"{k}: {v}")
        return reg_dict
            
            # 在这里可以对接收到的data进行解析
    else:
        print("无数据接收")
    return
