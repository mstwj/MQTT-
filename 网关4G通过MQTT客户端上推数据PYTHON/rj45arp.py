import uctypes

# ==============================================
# 查看 ARP 表（你已经能用的）
# ==============================================
def arp():
    print("\n===== ESP32 ARP 表 (arp -a) =====")
    ARP_TABLE_SIZE = 12
    ETH_ARP_USED = 0x10
    ETH_ARP_STATIC = 0x02
    ARP_BASE = 0x3FCA28FC
    ENTRY_SIZE = 28

    count = 0
    for i in range(ARP_TABLE_SIZE):
        entry_bytes = uctypes.bytearray_at(ARP_BASE + i * ENTRY_SIZE, ENTRY_SIZE)
        state = entry_bytes[0]
        if not (state & ETH_ARP_USED):
            continue

        ip = "{}.{}.{}.{}".format(entry_bytes[8], entry_bytes[9], entry_bytes[10], entry_bytes[11])
        mac = ":".join("%02X" % b for b in entry_bytes[12:18])
        typ = "静态" if (state & ETH_ARP_STATIC) else "动态"
        print(f"IP: {ip:16} MAC: {mac}  {typ}")
        count += 1
    if count == 0:
        print("ARP 表为空")
    print("==================================\n")

# ==============================================
# 新增：添加静态 ARP（arp -s IP MAC）
# 使用方法：arp_add("192.168.1.100", "00:11:22:33:44:55")
# ==============================================
def arp_add(ip_str, mac_str):
    # 1. 解析IP
    ip_parts = list(map(int, ip_str.split('.')))
    # 2. 解析MAC
    mac_parts = [int(b, 16) for b in mac_str.split(':')]

    ARP_BASE = 0x3FCA28FC
    ENTRY_SIZE = 28
    ARP_TABLE_SIZE = 12
    ETH_ARP_USED = 0x10

    # 先检查是否已经存在该IP，避免重复添加
    for i in range(ARP_TABLE_SIZE):
        addr = ARP_BASE + i * ENTRY_SIZE
        entry = uctypes.bytearray_at(addr, ENTRY_SIZE)
        if (entry[0] & ETH_ARP_USED):
            entry_ip = (entry[8], entry[9], entry[10], entry[11])
            if tuple(ip_parts) == entry_ip:
                print(f"⚠️ IP {ip_str} 已存在，无需重复添加")
                return

    # 找真正的空闲条目（entry[0] & 0x10 == 0 即为未使用）
    for i in range(ARP_TABLE_SIZE):
        addr = ARP_BASE + i * ENTRY_SIZE
        entry = uctypes.bytearray_at(addr, ENTRY_SIZE)
        if not (entry[0] & ETH_ARP_USED):  # 只有未使用的条目才是可写的
            # 写入状态：静态 + 已使用
            entry[0] = 0x10 | 0x02
            # 写入IP（偏移8）
            entry[8:12] = bytes(ip_parts)
            # 写入MAC（偏移12）
            entry[12:18] = bytes(mac_parts)
            print(f"✅ 静态ARP添加成功：{ip_str} -> {mac_str}")
            return

    print("❌ ARP 表已满，无法添加")

# ==============================================
# 清空 ARP 表（可选）
# ==============================================
def arp_clear():
    ARP_BASE = 0x3FCA28FC
    ENTRY_SIZE = 28
    ARP_TABLE_SIZE = 12
    for i in range(ARP_TABLE_SIZE):
        addr = ARP_BASE + i * ENTRY_SIZE
        entry = uctypes.bytearray_at(addr, ENTRY_SIZE)
        entry[0] = 0
    print("🗑️ 已清空 ARP 表")