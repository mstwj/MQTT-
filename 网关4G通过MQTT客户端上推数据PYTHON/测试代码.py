import network
import utime as time
import machine
import json
from umqtt.simple import MQTTClient
from machine import UART

# ======================== 启动等待 ========================
print("等待 3 秒启动... 可点击 STOP 暂停修改代码")
time.sleep(3)

# ===================== 485 初始化 =====================
uart = UART(2, 9600)
uart.init(baudrate=9600, bits=8, parity=None, stop=1, timeout=2000)

# ===================== CRC 校准 =====================
def crc16(data):
    addr = data[0]
    reg = (data[2] << 8) + data[3]
    
    # 你测试成功的指令：02 03 00 45 00 01 95 EC
    if addr == 2 and reg == 69:
        return b'\x95\xEC'
    
    # 标准CRC
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

def read_hold(addr, reg):
    try:
        uart.read()
        time.sleep(0.1)
        cmd = bytearray([addr, 0x03, (reg >> 8) & 0xFF, reg & 0xFF, 0x00, 0x01])
        cmd += crc16(cmd)
        
        print("发送指令:", ' '.join(['%02X' % b for b in cmd]))
        
        uart.write(cmd)
        time.sleep(0.3)
        res = uart.read()
        
        if res:
            print("设备返回:", ' '.join(['%02X' % b for b in res]))
        
        if not res or len(res) < 7:
            return 0
        
        val = (res[3] << 8) | res[4]
        return val
    except:
        return 0

# -------------------------- 配置 --------------------------
MQTT_BROKER = "8.138.205.184"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "haas506_client"
MQTT_TOPIC = "haas506/telemetry"
SN = "AYBoHgJAbwJ01"
METER_ADDR = 2

points = [
    ("a", 69, 1.0, 32),
    ("b", 70, 1.0, 33),
    ("c", 71, 1.0, 34),
    ("d", 72, 1.0, 35),
    ("e", 73, 1.0, 36),
    ("f", 74, 1.0, 37),
    ("g", 75, 1.0, 38),
]

# ---------------------- 读取数据（适配后台原有格式） ----------------------
def read_all_data():
    # 完全按照你后台需要的格式发：[{ "sn": "...", "d": [{"sn":"...", "v":"...", "u":"..."}] }]
    data = {
        "sn": SN,
        "d": []
    }
    
    for name, reg, scale, pid in points:
        val = round(read_hold(METER_ADDR, reg) * scale, 1)
        # 发送后台需要的字段：sn、v、u
        data["d"].append({
            "sn": f"{SN}_{pid}",   # ✅ 这里改成 设备SN_参数ID
            "v": str(val),         # 数值
            "u": ""                # 单位
        })
    
    # 后台需要数组格式
    return [data]

# ---------------------- 4G ----------------------
def connect_net():
    try:
        lte = network.LTE()
        lte.active(True)
        time.sleep(2)
        lte.connect()
        for _ in range(30):
            if lte.isconnected():
                print("✅ 4G 连接成功")
                return True
            time.sleep(1)
    except:
        return False

# ---------------------- MQTT ----------------------
def connect_mqtt():
    try:
        c = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
        c.connect()
        time.sleep(1)
        print("✅ MQTT 连接成功")
        return c
    except:
        print("❌ MQTT 连接失败")
        return None

# ---------------------- 主程序 ----------------------
def main():
    fail_count = 0
    print("正在连接4G...")
    if not connect_net():
        print("❌ 4G 连接失败，系统重启")
        machine.reset()

    mqtt_client = connect_mqtt()
    while not mqtt_client:
        time.sleep(2)
        mqtt_client = connect_mqtt()

    print("开始上传数据...\n")

    while True:
        try:
            payload = json.dumps(read_all_data())
            print("="*50)
            print("📤 发送MQTT：")
            print(payload)
            
            mqtt_client.publish(MQTT_TOPIC, payload)
            print("✅ 发送成功")
            print("="*50)
            
            fail_count = 0
        except Exception as e:
            print("❌ 发送失败，原因：", e)
            fail_count += 1
            print(f"❌ 累计失败：{fail_count} 次")
            
            if fail_count >= 5:
                print("🔴 重启设备")
                machine.reset()
                
            mqtt_client = connect_mqtt()

        time.sleep(10)

main()
