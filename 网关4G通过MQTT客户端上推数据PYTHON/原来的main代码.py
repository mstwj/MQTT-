import network
import utime as time
import machine
import json
from umqtt.simple import MQTTClient
from machine import UART

print("Wait 3 seconds...")
time.sleep(3)

uart = UART(2, 9600)
uart.init(baudrate=9600, bits=8, parity=None, stop=1, timeout=800)

# -------------------------- CRC16 校验 --------------------------
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

# -------------------------- 批量读连续寄存器 --------------------------
def read_hold_bulk(addr, start_reg, count):
    try:
        uart.read()
        time.sleep(0.02)
        cmd = bytearray([addr, 0x03,
                        (start_reg >> 8) & 0xFF, start_reg & 0xFF,
                        (count >> 8) & 0xFF, count & 0xFF])
        cmd += crc16(cmd)
        
        # ========== 打印发送指令 ==========
        print("【UART 发送】:", cmd.hex())
        
        uart.write(cmd)
        time.sleep(0.1)
        res = uart.read()
        
        # ========== 打印接收数据 ==========
        if res:
            print("【UART 接收】:", res.hex())
        else:
            print("【UART 接收】: 无数据")
        
        expected_len = 5 + 2 * count
        if not res or len(res) < expected_len:
            return [0]*count
        
        values = []
        for i in range(count):
            pos = 3 + i*2
            val = (res[pos] << 8) | res[pos+1]
            values.append(val)
        return values
    except Exception as e:
        print("读取异常:", e)
        return [0]*count

# -------------------------- 配置 --------------------------
MQTT_BROKER = "8.138.205.184"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "hunbu_controller_client"
MQTT_TOPIC = "hunbu/telemetry"
SN = "AYBoHgJAbwJ01"
METER_ADDR = 2

# -------------------------- 点位表 --------------------------
points = [
    ("system_phase_a_voltage", 69, 1.0, "", 32)
]

# -------------------------- 稳定读取：读50个发50个 --------------------------
def read_and_send_batch(batch_points):
    reg_map = {}
    for p in batch_points:
        reg = p[1]
        reg_map[reg] = list(p)

    sorted_regs = sorted(reg_map.keys())
    blocks = []
    if not sorted_regs:
        return []

    current_start = sorted_regs[0]
    current_end = sorted_regs[0]
    for r in sorted_regs[1:]:
        if r == current_end + 1:
            current_end = r
        else:
            blocks.append((current_start, current_end - current_start + 1))
            current_start = r
            current_end = r
    blocks.append((current_start, current_end - current_start + 1))

    for s, cnt in blocks:
        vals = read_hold_bulk(METER_ADDR, s, cnt)
        for i in range(cnt):
            r = s + i
            if r in reg_map:
                reg_map[r][4] = vals[i]

    send_list = []
    for p in batch_points:
        name, r, scale, unit, pid = p
        val_raw = reg_map[r][4]
        val_real = round(val_raw * scale, 2)
        send_list.append({
            "sn": f"{SN}_{pid}",
            "v": val_real,
            "u": ""
        })
    return send_list

# -------------------------- 网络 --------------------------
def connect_net():
    try:
        lte = network.LTE()
        lte.active(True)
        time.sleep(1)
        lte.connect()
        for _ in range(20):
            if lte.isconnected():
                print("✅ 4G OK")
                return True
            time.sleep(0.5)
    except:
        return False

def connect_mqtt():
    try:
        c = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
        c.connect()
        print("✅ MQTT OK")
        return c
    except:
        print("❌ MQTT 失败")
        return None

# -------------------------- 主程序（稳到爆） --------------------------
def main():
    if not connect_net():
        machine.reset()

    mqtt_client = connect_mqtt()
    while not mqtt_client:
        time.sleep(1)
        mqtt_client = connect_mqtt()

    BATCH_SIZE = 50  # 一次读50发50
    LOOP_DELAY = 10

    while True:
        print("🔄 开始一轮采集")
        index = 0
        total = len(points)
        
        while index < total:
            end = min(index + BATCH_SIZE, total)
            current = points[index:end]
            
            try:
                # 读 → 发，一步到位
                data = read_and_send_batch(current)
                payload = json.dumps(data)
                mqtt_client.publish(MQTT_TOPIC, payload)
                print(f"✅ 发送 {index+1} ~ {end}")
                index = end
                time.sleep(1)
            except:
                print("⚠️ 异常，重连...")
                mqtt_client = connect_mqtt()
                time.sleep(2)

        print("🎉 244 点全部发送完成！\n")
        time.sleep(LOOP_DELAY)

main()
