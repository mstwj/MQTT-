# main.py - 主程序（UDP发送+Modbus读取）
import network
import usocket as socket
import time
# 导入Modbus模块
import modbus_485

# #################### 配置项 ####################
UDP_SERVER_IP = '192.168.0.100'
UDP_SERVER_PORT = 8080
CLIENT_IP = '192.168.0.80'
CLIENT_SUBNET = '255.255.255.0'
CLIENT_GATEWAY = '192.168.0.1'  # 直连网关=服务器IP
CLIENT_DNS = '8.8.8.8'
SEND_INTERVAL = 3
# ################################################

# 👉 手动设置你的以太网MAC地址（自己随便改，只要格式正确）
ETH_MAC = b'\x00\x11\x22\x33\x44\x55'

# 👉 目标设备MAC（你想发给谁，就填谁的MAC）
TARGET_MAC = b'\xAA\xBB\xCC\xDD\xEE\xFF'  # 改成接收端真实MAC

# 极简以太网初始化
def init_ethernet_simple():
    eth = network.LAN()
    # ✅ 手动设置 MAC（解决 00:00:00 问题）
    eth.config(mac=ETH_MAC)
    eth.active(True)
     # ========== 我加的：获取 RJ45 网口 MAC ==========
    mac = eth.config('mac')
    mac_str = ':'.join(['%02X' % b for b in mac])
    print("="*40)
    print("✅ 你的 RJ45 以太网 MAC 地址 =", mac_str)
    print("="*40)
    print("✅ 目标MAC:", ':'.join(['%02X' % b for b in TARGET_MAC]))
    
    eth.ifconfig((CLIENT_IP, CLIENT_SUBNET, CLIENT_GATEWAY, CLIENT_DNS))
    time.sleep(2)
    print("🔌 以太网初始化完成")
    return eth

# 读取Modbus电压数据
def read_modbus_voltage():
    """调用Modbus模块读取电压值"""
    try:
        # 调用modbus_485模块的H03函数
        vt_tuple = modbus_485.H03(11, 4, 1)
        vt = vt_tuple[0] * 0.1
        register_tuple = modbus_485.H03(11, 82, 1)
        voltage = register_tuple[0] * vt * 0.1
        return voltage
    except Exception as e:
        print(f"❌ 读取Modbus失败: {e}")
        return None

# 主函数
def main():
    eth = init_ethernet_simple()
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((CLIENT_IP, 8888))
    
    print("\n🚀 开始发送Modbus电压数据（10秒间隔）...")
    while True:
        # 1. 读取Modbus电压
        voltage = read_modbus_voltage()
        if voltage is None:
            send_data = "Modbus read failed"
        else:
            send_data = f"Voltage: {voltage:.2f}V"
        
        # 2. UDP发送电压数据
        try:
            udp_sock.sendto(send_data.encode('utf-8'), (UDP_SERVER_IP, UDP_SERVER_PORT))
            print(f"📤 已发送: {send_data}")
        except Exception as e:
            print(f"❌ UDP发送失败: {e}")
        
        time.sleep(SEND_INTERVAL)

if __name__ == '__main__':
    main()
