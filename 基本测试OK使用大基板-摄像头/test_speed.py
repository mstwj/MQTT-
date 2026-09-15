# test_speed_pro.py - 极限测速脚本
import time
import network
import usocket as socket

WIFI_SSID = "Aoyan"
WIFI_PASS = "A15344803439b"
PC_IP = "192.168.0.118"
PC_PORT = 9999

# 1. 连 Wi-Fi 并关闭节能模式
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep_ms(500)

# 【核心大招1】关闭 Wi-Fi 节能，让射频全速全功率输出
try:
    wlan.config(pm=0xa411) # 某些固件关闭节能的参数，或者直接用下面通用写法
except:
    pass

print("✅ Wi-Fi 已连接，IP:", wlan.ifconfig()[0])

# 2. 建立 TCP 连接并测速
print(f"🔗 正在连接测试服务端 {PC_IP}:{PC_PORT}...")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 【核心大招2】禁用 Nagle 算法，实现数据包“发完即走”
try:
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
except:
    pass

s.connect((PC_IP, PC_PORT))
print("🚀 TCP 连接成功，开始极限测速...")

# 构造一个 5KB 的虚拟图片数据（模拟真实 QVGA 帧大小）
dummy_data = b"\xFF" * 5120

total_bytes = 0
start_tick = time.ticks_ms()
test_duration = 5000  # 测试 5 秒钟

while time.ticks_diff(time.ticks_ms(), start_tick) < test_duration:
    try:
        # 发送 4 字节长度 + 真实数据
        s.send(len(dummy_data).to_bytes(4, 'big'))
        s.send(dummy_data)
        total_bytes += len(dummy_data)
    except Exception as e:
        print("发送中断:", e)
        break

s.close()

elapsed_sec = time.ticks_diff(time.ticks_ms(), start_tick) / 1000.0
speed_kb = (total_bytes / 1024) / elapsed_sec

print(f"📊 极限测速结果：")
print(f"总共成功上传: {total_bytes / 1024:.2f} KB")
print(f"极限平均上传速度: {speed_kb:.2f} KB/s")