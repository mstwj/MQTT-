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

def read_hold(addr, reg):
    try:
        uart.read()
        time.sleep(0.03)
        cmd = bytearray([addr, 0x03, (reg >> 8) & 0xFF, reg & 0xFF, 0x00, 0x01])
        cmd += crc16(cmd)
        uart.write(cmd)
        time.sleep(0.12)
        res = uart.read()
        if not res or len(res) < 7:
            return 0
        val = (res[3] << 8) | res[4]
        return val
    except:
        return 0

# -------------------------- 配置 --------------------------
MQTT_BROKER = "8.138.205.184"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "hunbu_controller_client"
MQTT_TOPIC = "hunbu/telemetry"
SN = "AYBoHgJAbwJ01"
METER_ADDR = 1

# -------------------------- 点位表 --------------------------
points = [
    ("module1_capacity", 0, 0.1, "kVar", 1),
    ("module2_capacity", 1, 0.1, "kVar", 2),
    ("module3_capacity", 2, 0.1, "kVar", 3),
    ("module4_capacity", 3, 0.1, "kVar", 4),
    ("module5_capacity", 4, 0.1, "kVar", 5),
    ("switch_mode", 36, 1.0, "", 6),
    ("switch_strategy", 37, 1.0, "", 7),
    ("switch_on_pf", 38, 0.01, "", 8),
    ("switch_off_pf", 39, 0.01, "", 9),
    ("system_current_ratio", 40, 1.0, "", 10),
    ("cabinet_current_ratio", 41, 1.0, "", 11),
    ("switch_on_delay", 42, 1.0, "", 12),
    ("switch_off_delay", 43, 1.0, "", 13),
    ("switch_interval", 44, 1.0, "", 14),
    ("discharge_delay", 45, 1.0, "", 15),
    ("switch_on_capacity_coeff", 46, 0.01, "", 16),
    ("switch_off_capacity_coeff", 47, 0.01, "", 17),
    ("power_company_code", 48, 1.0, "", 18),
    ("protect_switch_off_delay", 49, 1.0, "", 19),
    ("protect_detect_delay", 50, 1.0, "", 20),
    ("over_voltage_threshold", 51, 1.0, "", 21),
    ("under_voltage_threshold", 52, 1.0, "", 22),
    ("thdu_upper_limit", 53, 1.0, "", 23),
    ("thdi_upper_limit", 54, 1.0, "", 24),
    ("cabinet_fan_start_temp", 62, 1.0, "℃", 25),
    ("cabinet_thdi_upper_limit", 63, 1.0, "", 26),
    ("switch_reference_condition", 64, 1.0, "", 27),
    ("terminal_device_code", 65, 1.0, "", 28),
    ("phase_a_cabinet_thdi", 66, 1.0, "%", 29),
    ("phase_b_cabinet_thdi", 67, 1.0, "%", 30),
    ("phase_c_cabinet_thdi", 68, 1.0, "%", 31),
    ("system_phase_a_voltage", 69, 1.0, "", 32),
    ("system_phase_a_current", 70, 1.0, "", 33),
    ("cabinet_phase_a_current", 71, 1.0, "", 34),
    ("system_phase_a_frequency", 72, 1.0, "", 35),
    ("system_phase_a_active_power", 73, 1.0, "", 36),
    ("system_phase_a_reactive_power", 74, 1.0, "", 37),
    ("system_phase_a_apparent_power", 75, 1.0, "", 38),
    ("phase_a_power_factor", 76, 1.0, "", 39),
    ("phase_a_thdu", 77, 1.0, "%", 40),
    ("phase_a_thdi", 78, 1.0, "%", 41),
    ("system_phase_b_voltage", 79, 1.0, "", 42),
    ("system_phase_b_current", 80, 1.0, "", 43),
    ("cabinet_phase_b_current", 81, 1.0, "", 44),
    ("system_phase_b_frequency", 82, 1.0, "", 45),
    ("system_phase_b_active_power", 83, 1.0, "", 46),
    ("system_phase_b_reactive_power", 84, 1.0, "", 47),
    ("system_phase_b_apparent_power", 85, 1.0, "", 48),
    ("phase_b_power_factor", 86, 1.0, "", 49),
    ("phase_b_thdu", 87, 1.0, "%", 50),
    ("phase_b_thdi", 88, 1.0, "%", 51),
    ("system_phase_c_voltage", 89, 1.0, "", 52),
    ("system_phase_c_current", 90, 1.0, "", 53),
    ("cabinet_phase_c_current", 91, 1.0, "", 54),
    ("system_phase_c_frequency", 92, 1.0, "", 55),
    ("system_phase_c_active_power", 93, 1.0, "", 56),
    ("system_phase_c_reactive_power", 94, 1.0, "", 57),
    ("system_phase_c_apparent_power", 95, 1.0, "", 58),
    ("phase_c_power_factor", 96, 1.0, "", 59),
    ("phase_c_thdu", 97, 1.0, "%", 60),
    ("phase_c_thdi", 98, 1.0, "%", 61),
    ("reg_427", 427, 1.0, "", 62),
    ("reg_428", 428, 1.0, "", 63),
    ("reg_429", 429, 1.0, "", 64),
    ("reg_430", 430, 1.0, "", 65),
    ("reg_431", 431, 1.0, "", 66),
    ("reg_432", 432, 1.0, "", 67),
    ("reg_433", 433, 1.0, "", 68),
    ("reg_434", 434, 1.0, "", 69),
    ("reg_435", 435, 1.0, "", 70),
    ("reg_1099", 1099, 1.0, "", 71),
    ("reg_1100", 1100, 1.0, "", 72),
    ("reg_1101", 1101, 1.0, "", 73),
    ("reg_1102", 1102, 1.0, "", 74),
    ("reg_1103", 1103, 1.0, "", 75),
    ("reg_1104", 1104, 1.0, "", 76),
    ("reg_1105", 1105, 1.0, "", 77),
    ("reg_1106", 1106, 1.0, "", 78),
    ("reg_1107", 1107, 1.0, "", 79),
    ("reg_1108", 1108, 1.0, "", 80),
    ("reg_1166", 1166, 1.0, "", 81),
    ("reg_1167", 1167, 1.0, "", 82),
    ("reg_1168", 1168, 1.0, "", 83),
    ("reg_1169", 1169, 1.0, "", 84),
    ("reg_1170", 1170, 1.0, "", 85),
    ("reg_1171", 1171, 1.0, "", 86),
    ("reg_1172", 1172, 1.0, "", 87),
    ("reg_1173", 1173, 1.0, "", 88),
    ("reg_1174", 1174, 1.0, "", 89),
    ("reg_1175", 1175, 1.0, "", 90),
    ("reg_1233", 1233, 1.0, "", 91),
    ("reg_1234", 1234, 1.0, "", 92),
    ("reg_1235", 1235, 1.0, "", 93),
    ("reg_1236", 1236, 1.0, "", 94),
    ("reg_1237", 1237, 1.0, "", 95),
    ("reg_1238", 1238, 1.0, "", 96),
    ("reg_1239", 1239, 1.0, "", 97),
    ("reg_1240", 1240, 1.0, "", 98),
    ("reg_1241", 1241, 1.0, "", 99),
    ("reg_1242", 1242, 1.0, "", 100),
    ("reg_1300", 1300, 1.0, "", 101),
    ("reg_1301", 1301, 1.0, "", 102),
    ("reg_1302", 1302, 1.0, "", 103),
    ("reg_1303", 1303, 1.0, "", 104),
    ("reg_1304", 1304, 1.0, "", 105),
    ("reg_1305", 1305, 1.0, "", 106),
    ("reg_1306", 1306, 1.0, "", 107),
    ("reg_1307", 1307, 1.0, "", 108),
    ("reg_1308", 1308, 1.0, "", 109),
    ("reg_1309", 1309, 1.0, "", 110),
    ("reg_1573", 1573, 1.0, "%", 111),
    ("reg_1574", 1574, 1.0, "%", 112),
    ("reg_1575", 1575, 1.0, "%", 113),
    ("reg_1576", 1576, 1.0, "%", 114),
    ("reg_1577", 1577, 1.0, "%", 115),
    ("reg_1578", 1578, 1.0, "%", 116),
    ("reg_1579", 1579, 1.0, "%", 117),
    ("reg_1580", 1580, 1.0, "%", 118),
    ("reg_1581", 1581, 1.0, "%", 119),
    ("reg_1582", 1582, 1.0, "%", 120),
    ("reg_1583", 1583, 1.0, "%", 121),
    ("reg_1584", 1584, 1.0, "%", 122),
    ("reg_1585", 1585, 1.0, "%", 123),
    ("reg_1586", 1586, 1.0, "%", 124),
    ("reg_1587", 1587, 1.0, "%", 125),
    ("reg_1588", 1588, 1.0, "%", 126),
    ("reg_1589", 1589, 1.0, "%", 127),
    ("reg_1590", 1590, 1.0, "%", 128),
    ("reg_1591", 1591, 1.0, "%", 129),
    ("reg_1592", 1592, 1.0, "%", 130),
    ("reg_1593", 1593, 1.0, "%", 131),
    ("reg_1594", 1594, 1.0, "%", 132),
    ("reg_1595", 1595, 1.0, "%", 133),
    ("reg_1596", 1596, 1.0, "%", 134),
    ("reg_1597", 1597, 1.0, "%", 135),
    ("reg_1598", 1598, 1.0, "%", 136),
    ("reg_1599", 1599, 1.0, "%", 137),
    ("reg_1600", 1600, 1.0, "%", 138),
    ("reg_1601", 1601, 1.0, "%", 139),
    ("reg_1602", 1602, 1.0, "%", 140),
    ("reg_1603", 1603, 1.0, "%", 141),
    ("reg_1604", 1604, 1.0, "%", 142),
    ("reg_1605", 1605, 1.0, "%", 143),
    ("reg_1606", 1606, 1.0, "%", 144),
    ("reg_1607", 1607, 1.0, "%", 145),
    ("reg_1608", 1608, 1.0, "%", 146),
    ("reg_1609", 1609, 1.0, "%", 147),
    ("reg_1610", 1610, 1.0, "%", 148),
    ("reg_1611", 1611, 1.0, "%", 149),
    ("reg_1612", 1612, 1.0, "%", 150),
    ("reg_1613", 1613, 1.0, "%", 151),
    ("reg_1614", 1614, 1.0, "%", 152),
    ("reg_1615", 1615, 1.0, "%", 153),
    ("reg_1616", 1616, 1.0, "%", 154),
    ("reg_1617", 1617, 1.0, "%", 155),
    ("reg_1618", 1618, 1.0, "%", 156),
    ("reg_1619", 1619, 1.0, "%", 157),
    ("reg_1620", 1620, 1.0, "%", 158),
    ("reg_1621", 1621, 1.0, "%", 159),
    ("reg_100", 100, 1.0, "", 160),
    ("reg_101", 101, 1.0, "", 161),
    ("reg_102", 102, 1.0, "", 162),
    ("reg_103", 103, 1.0, "", 163),
    ("reg_104", 104, 1.0, "", 164),
    ("reg_105", 105, 1.0, "", 165),
    ("reg_106", 106, 1.0, "", 166),
    ("reg_107", 107, 1.0, "", 167),
    ("reg_108", 108, 1.0, "", 168),
    ("reg_109", 109, 1.0, "", 169),
    ("reg_110", 110, 1.0, "", 170),
    ("reg_111", 111, 1.0, "", 171),
    ("reg_112", 112, 1.0, "", 172),
    ("reg_113", 113, 1.0, "", 173),
    ("reg_114", 114, 1.0, "", 174),
    ("reg_115", 115, 1.0, "", 175),
    ("reg_116", 116, 1.0, "", 176),
    ("reg_117", 117, 1.0, "", 177),
    ("reg_118", 118, 1.0, "", 178),
    ("reg_119", 119, 1.0, "", 179),
    ("reg_120", 120, 1.0, "", 180),
    ("reg_121", 121, 1.0, "", 181),
    ("reg_122", 122, 1.0, "", 182),
    ("reg_123", 123, 1.0, "", 183),
    ("reg_124", 124, 1.0, "", 184),
    ("reg_125", 125, 1.0, "", 185),
    ("reg_126", 126, 1.0, "", 186),
    ("reg_127", 127, 1.0, "", 187),
    ("reg_128", 128, 1.0, "", 188),
    ("reg_129", 129, 1.0, "", 189),
    ("reg_130", 130, 1.0, "", 190),
    ("reg_131", 131, 1.0, "", 191),
    ("reg_132", 132, 1.0, "", 192),
    ("reg_133", 133, 1.0, "", 193),
    ("reg_134", 134, 1.0, "", 194),
    ("reg_135", 135, 1.0, "", 195),
    ("reg_136", 136, 1.0, "", 196),
    ("reg_137", 137, 1.0, "", 197),
    ("reg_138", 138, 1.0, "", 198),
    ("reg_139", 139, 1.0, "", 199),
    ("reg_140", 140, 1.0, "", 200),
    ("reg_141", 141, 1.0, "", 201),
    ("reg_142", 142, 1.0, "", 202),
    ("reg_143", 143, 1.0, "", 203),
    ("reg_144", 144, 1.0, "", 204),
    ("reg_145", 145, 1.0, "", 205),
    ("reg_146", 146, 1.0, "", 206),
    ("reg_147", 147, 1.0, "", 207),
    ("reg_148", 148, 1.0, "", 208),
    ("reg_149", 149, 1.0, "", 209),
    ("reg_150", 150, 1.0, "", 210),
    ("reg_151", 151, 1.0, "", 211),
    ("reg_152", 152, 1.0, "", 212),
    ("reg_153", 153, 1.0, "", 213),
    ("reg_154", 154, 1.0, "", 214),
    ("reg_155", 155, 1.0, "", 215),
    ("reg_156", 156, 1.0, "", 216),
    ("reg_157", 157, 1.0, "", 217),
    ("reg_158", 158, 1.0, "", 218),
    ("reg_159", 159, 1.0, "", 219),
    ("reg_160", 160, 1.0, "", 220),
    ("reg_161", 161, 1.0, "", 221),
    ("reg_162", 162, 1.0, "", 222),
    ("reg_163", 163, 1.0, "", 223),
    ("reg_164", 164, 1.0, "", 224),
    ("reg_165", 165, 1.0, "", 225),
    ("reg_166", 166, 1.0, "", 226),
    ("reg_167", 167, 1.0, "", 227),
    ("reg_168", 168, 1.0, "", 228),
    ("reg_169", 169, 1.0, "", 229),
    ("reg_170", 170, 1.0, "", 230),
    ("reg_171", 171, 1.0, "", 231),
    ("reg_172", 172, 1.0, "", 232),
    ("reg_173", 173, 1.0, "", 233),
    ("reg_174", 174, 1.0, "", 234),
    ("reg_175", 175, 1.0, "", 235),
    ("reg_176", 176, 1.0, "", 236),
    ("reg_177", 177, 1.0, "", 237),
    ("reg_178", 178, 1.0, "", 238),
    ("reg_179", 179, 1.0, "", 239),
    ("reg_180", 180, 1.0, "", 240),
    ("reg_181", 181, 1.0, "", 241),
    ("reg_182", 182, 1.0, "", 242),
    ("reg_183", 183, 1.0, "", 243),
    ("reg_184", 184, 1.0, "", 244),
]

# ---------------------- 分批函数 ----------------------
def read_batch(points_batch):
    data = {"sn": SN, "d": []}
    for name, reg, scale, unit, pid in points_batch:
        val = round(read_hold(METER_ADDR, reg) * scale, 2)
        data["d"].append({
            "sn": f"{SN}_{pid}",
            "v": val,
            "u": f""
        })
    return data

def connect_net():
    try:
        lte = network.LTE()
        lte.active(True)
        time.sleep(2)
        lte.connect()
        for _ in range(30):
            if lte.isconnected():
                print("✅ 4G connected")
                return True
            time.sleep(1)
    except:
        return False

def connect_mqtt():
    try:
        c = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
        c.connect()
        time.sleep(0.3)
        print("✅ MQTT connected")
        return c
    except:
        print("❌ MQTT fail")
        return None

# ---------------------- 主程序提速配置 ----------------------
def main():
    if not connect_net():
        machine.reset()

    mqtt_client = connect_mqtt()
    while not mqtt_client:
        time.sleep(2)
        mqtt_client = connect_mqtt()

    BATCH_SIZE = 30
    INTERVAL = 0.2    # 同批次间隔 原1s→0.2s
    LOOP_INTERVAL = 8 # 整轮等待原60s→15s

    while True:
        index = 0
        total_points = len(points)
        while index < total_points:
            end_idx = min(index + BATCH_SIZE, total_points)
            current_batch = points[index:end_idx]
            
            try:
                data = read_batch(current_batch)
                payload = json.dumps(data["d"])
                mqtt_client.publish(MQTT_TOPIC, payload)
                print(f"✅ Sent {index+1} ~ {end_idx}")
            except:
                print("❌ Send failed, reconnecting...")
                mqtt_client = connect_mqtt()
                time.sleep(1)
                continue

            index = end_idx
            time.sleep(INTERVAL)

        print("✅ All 244 points sent, waiting next round...")
        time.sleep(LOOP_INTERVAL)

main()
