import readnetandmqtt
import readdevice
import time
import json

# -------------------------- 主程序（稳到爆） --------------------------
def main():
    if not readnetandmqtt.connect_net():
        machine.reset()

    mqtt_client = readnetandmqtt.connect_mqtt()
    while not mqtt_client:
        time.sleep(1)
        mqtt_client = readnetandmqtt.connect_mqtt()

    while True:
        print("🔄 开始一轮采集")        
        #reg_all = readdevice.read_meter(0x0024,69) 24=36
        reg_all = readdevice.read_meter(0x0045,5)
        # 定义存储整批数据的字典
        payload_data = {}    
        if reg_all is not None:
            print("=================== 全部读取数据 ===================")
            for addr_dec in sorted(reg_all.keys()):
                raw_val = reg_all[addr_dec]
                if addr_dec in readdevice.reg_name_map:
                    info = readdevice.reg_name_map[addr_dec]
                    real_val = raw_val / info["scale"]
                    #print(f"地址{addr_dec} | {info['name']} | 原始值:{raw_val} | 实际值:{real_val} {info['unit']}")
                    # 存入字典，key用点位名称，值存原始值+实际值
                    payload_data[info["name"]] = {
                        "addr": addr_dec,
                        "raw": raw_val,
                        "real": real_val,
                        "scale": info["scale"]
                    }                                        
                else:
                    print(f"地址{addr_dec} | 未定义点位 | 原始值:{raw_val}")
                    # 未定义点位也一并存入
                    payload_data[f"undef_addr_{addr_dec}"] = {
                        "addr": addr_dec,
                        "raw": raw_val
                    }
            # ===== 一轮采集完成，一次性推送全部数据到MQTT =====
            try:
                # 转json字符串
                mqtt_json = json.dumps(payload_data)
                print("{mqtt_json}")
                # 发布主题，自行修改成你需要的topic
                #mqtt_topic = "meter/all_data"
                mqtt_client.publish(readnetandmqtt.MQTT_TOPIC, mqtt_json)
                print(f"✅ MQTT批量上报完成，主题:{readnetandmqtt.MQTT_TOPIC}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ MQTT发送失败：{e}")                
        time.sleep(2)
        
main()
