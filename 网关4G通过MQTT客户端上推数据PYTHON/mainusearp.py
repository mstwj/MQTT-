import network
import usocket as socket
import time
import modbus_485
import uctypes
from rj45arp import arp, arp_add  # 导入函数



# #################### 静态配置 ####################
UDP_SERVER_IP = '192.168.0.100'
UDP_SERVER_PORT = 8080
CLIENT_IP = '192.168.0.80'
CLIENT_SUBNET = '255.255.255.0'
CLIENT_GATEWAY = '192.168.0.1'
CLIENT_DNS = '8.8.8.8'
SEND_INTERVAL = 3

ETH_MAC = b'\x00\x11\x22\x33\x44\x55'
# 目标服务器静态 MAC（必须正确）
TARGET_MAC = b'\xAA\xBB\xCC\xDD\xEE\xFF'
# ################################################

# --------------------------
# 1. 以太网初始化
# --------------------------
def init_ethernet_simple():
    eth = network.LAN()
    eth.config(mac=ETH_MAC)
    eth.active(True)
    eth.ifconfig((CLIENT_IP, CLIENT_SUBNET, CLIENT_GATEWAY, CLIENT_DNS))
    time.sleep(2)
    print("🔌 以太网初始化完成")
    return eth


# --------------------------
# 3. Modbus 读取
# --------------------------
def read_modbus_voltage():
    try:
        vt_tuple = modbus_485.H03(11, 4, 1)
        vt = vt_tuple[0] * 0.1
        register_tuple = modbus_485.H03(11, 82, 1)
        voltage = register_tuple[0] * vt * 0.1
        return voltage
    except Exception as e:
        print(f"❌ Modbus 读取失败: {e}")
        return None

# --------------------------
# 4. 主程序（纯静态发送）
# --------------------------
def main():
    eth = init_ethernet_simple()
    # 启动时写入静态 ARP（只写一次，之后不再广播）
    target_mac_str = ":".join("%02X" % b for b in TARGET_MAC)
    
    arp()    
    arp_add(UDP_SERVER_IP, target_mac_str)
    arp()    

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((CLIENT_IP, 8888))
    print("\n🚀 开始【纯静态】发送 UDP（无 ARP 广播）...")

    while True:
        voltage = read_modbus_voltage()
        send_data = f"Voltage: {voltage:.2f}V" if voltage else "Modbus error"

        try:
            # 直接发送，依赖静态 ARP
            udp_sock.sendto(send_data.encode(), (UDP_SERVER_IP, UDP_SERVER_PORT))
            print(f"✅ 已发送: {send_data}")
        except Exception as e:
            print(f"❌ 发送失败: {e}")

        time.sleep(SEND_INTERVAL)

if __name__ == '__main__':
    main()
