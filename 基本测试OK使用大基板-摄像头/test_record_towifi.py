# main.py - AI 语音助手 + AI 画图（生产修复与优化版）
import gc
import time
from machine import Pin
import network
import usocket as socket
from asr_client import transcribe_wav
from wifi_manager import (
    connect_router_wifi,
    is_sta_connected,
    load_wifi_config,
    start_ap_web_server,
)

from audio_recorder import AudioRecorder

BOOT_PIN = 0     # ESP32-S3 板载 Boot 键 GPIO0 (语音对话)
recorder = AudioRecorder()
button = Pin(14, Pin.IN, Pin.PULL_UP)  # IO14: 录音按键

# ==========================================
# 2. 网络初始化
# ==========================================
ssid, pwd = load_wifi_config()
connect_ok = False
current_ip = None

wifi_online_last = False

if ssid and pwd:
    print(f"正在连接无线网络: {ssid}...")
    try:
        connect_ok, current_ip = connect_router_wifi(ssid, pwd)
    except Exception as e:
        print(f"❌ Wi-Fi 连接过程异常: {e}")

is_processing = False

# ==========================================
# 3. 业务主循环
# ==========================================
while True:
    try:
        gc.collect()
        online = is_sta_connected()

        if online != wifi_online_last:
            if online:
                print(f"✅ 网络已连接, IP 地址: {current_ip}")
            else:
                print("⚠️ 网络连接中断！")
            wifi_online_last = online
        
        # 3. 监测 Boot 键 (GPIO0) - 正常 AI 语音对话
        if not is_processing and button.value() == 0:
            time.sleep_ms(20)
            if button.value() == 0:
                is_processing = True

                try:
                    time.sleep_ms(300)

                    print("\n🎙️ 听到按键，开始录音...")
                    recorder.record_to_wav(
                        "record.wav", button, max_seconds=15
                    )

                    if not is_sta_connected():
                        print("❌ 网络断开，无法上传音频！")
                        continue

                    print("🔍 正在识别语音...")
                    user_text = transcribe_wav("record.wav")
                    print(f"🗣️ 用户说: {user_text}")

                except Exception as req_err:
                    print(f"💥 业务交互流程发生捕获异常: {req_err}")
                    time.sleep(1.5)

                finally:
                    try:
                        recorder.close()
                    except:
                        pass
                    is_processing = False
                    gc.collect()

    except Exception as main_err:
        print(f"🚨 主循环异常捕获: {main_err}")
        is_processing = False
        time.sleep(1)

    time.sleep(0.05)
