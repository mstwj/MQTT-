import network
import utime as time
import machine
import json
from umqtt.simple import MQTTClient


# -------------------------- 配置 --------------------------
MQTT_BROKER = "8.138.205.184"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "hunbu_controller_client"
MQTT_TOPIC = "hunbu/telemetry"
SN = "AYBoHgJAbwJ01"
METER_ADDR = 2

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
