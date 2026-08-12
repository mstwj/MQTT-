from ai_client import chat_ask
from asr_client import transcribe_wav
from audio_play import play_wav
from audio_recorder import AudioRecorder
from machine import Pin
import time
from tts_client import text_to_speech  # 导入新封装的 TTS 模块
from wifi_manager import (
    connect_router_wifi,
    is_sta_connected,
    load_wifi_config,
    start_ap_web_server,
)

# 1. 硬件引脚配置
button = Pin(0, Pin.IN, Pin.PULL_UP)
recorder = AudioRecorder(sck_pin=5, ws_pin=6, sd_pin=4)

# 2. 加载 WiFi 配置并联网
ssid, pwd = load_wifi_config()
connect_ok = False
current_ip = None

# 空函数防止没接屏幕时 refresh_ui 报错
def refresh_ui(*args, **kwargs):
    pass

if ssid and pwd:
    print("正在连接无线网络...")
    connect_ok, current_ip = connect_router_wifi(ssid, pwd, refresh_ui)

# 连接失败则启动 AP 热点配网
if not connect_ok:
    print("WiFi 连接失败，启动配网模式...")
    start_ap_web_server(refresh_ui)

wifi_online_last = False

print("\n==================================")
print("👉 系统就绪！长按 Boot 键(GPIO0)开始说话")
print("==================================\n")

# 3. 业务主循环
while True:
    online = is_sta_connected()

    # WiFi 状态检测
    if online != wifi_online_last:
        if online:
            print(f"✅ 网络已连接, IP 地址: {current_ip}")
        else:
            print("⚠️ 网络连接中断！")
        wifi_online_last = online

    # 按键检测（低电平触发录音）
    if button.value() == 0:
        time.sleep_ms(20)  # 消抖
        if button.value() == 0:

            # --- Step 1: 录音 ---
            print("\n🎙️ 听到按键，开始录音...")
            recorder.record_to_wav("record.wav", button)

            if not is_sta_connected():
                print("❌ 网络断开，无法上传音频！")
                continue

            # --- Step 2: 语音识别 (ASR) ---
            print("🔍 正在识别语音...")
            user_text = transcribe_wav("record.wav")
            print(f"🗣️ 用户说: {user_text}")

            # --- Step 3: AI 大模型思考 ---
            if user_text and not user_text.startswith("Error"):
                print("🤖 正在思考回复...")
                ai_reply = chat_ask(user_text)
                print(f"💡 AI 回答: {ai_reply}")

                # --- Step 4: 文本转语音 (TTS) ---
                if ai_reply:
                    tts_success = text_to_speech(
                        ai_reply, filename="tts_output.wav"
                    )

                    # --- Step 5: 播放 AI 回答的音频 ---
                    if tts_success:
                        print("🔊 正在播放回答...")
                        play_wav("tts_output.wav")

            print("\n----------------------------------")
            print("👉 等待下一次按键...")

    time.sleep(0.05)