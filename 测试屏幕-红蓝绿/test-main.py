# main.py - 封装后的极简 AI 语音助手主流程

import time
from machine import Pin

from wifi_manager import (
    load_wifi_config,
    connect_router_wifi,
    start_ap_web_server,
    is_sta_connected,
)
from audio_recorder import AudioRecorder
from asr_client import transcribe_wav
from ai_client import chat_ask
from tts_client import text_to_speech
from audio_play import play_wav
from display_ui import UIManager  # 导入全新的 UI 模块

# ==========================================
# 1. 初始化 硬件、UI 与 全局对象
# ==========================================
button = Pin(0, Pin.IN, Pin.PULL_UP)
recorder = AudioRecorder(sck_pin=5, ws_pin=6, sd_pin=4)
ui = UIManager()  # 一键完成 SPI、ST7789 屏幕和 uFont 字库初始化

# 设置 UI 刷新全局回调函数 (适配 wifi_manager 内部调用)
def refresh_ui(title, content="", color=0xFFFF):
    ui.render(title, content, color)

# ==========================================
# 2. 网络初始化
# ==========================================
refresh_ui("网络连接", "正在连接 Wi-Fi，请稍候...", color=0xFFFF)

ssid, pwd = load_wifi_config()
connect_ok = False
current_ip = None

if ssid and pwd:
    print("正在连接无线网络...")
    connect_ok, current_ip = connect_router_wifi(ssid, pwd, refresh_ui)

if not connect_ok:
    print("WiFi 连接失败，启动配网模式...")
    refresh_ui("配网模式", "WiFi连接失败，请用手机连接热点配网", color=0xF800)
    start_ap_web_server(refresh_ui)

wifi_online_last = False
refresh_ui("AI 语音助手", "系统已就绪！长按 Boot 键开始说话", color=0x07E0)

print("\n==================================")
print("👉 系统就绪！长按 Boot 键(GPIO0)说话")
print("==================================\n")

# ==========================================
# 3. 业务主循环
# ==========================================
while True:
    online = is_sta_connected()

    # 网络状态变化监测
    if online != wifi_online_last:
        if online:
            print(f"✅ 网络已连接, IP 地址: {current_ip}")
            refresh_ui("网络已连接", f"IP: {current_ip}\n系统就绪，长按 Boot 键说话！", color=0x07E0)
        else:
            print("⚠️ 网络连接中断！")
            refresh_ui("网络中断", "WiFi 连接已断开，请检查网络设置", color=0xF800)
        wifi_online_last = online

    # 监测录音按键
    if button.value() == 0:
        time.sleep_ms(20)  # 消抖
        if button.value() == 0:

            # 步骤 1：录音
            print("\n🎙️ 听到按键，开始录音...")
            refresh_ui("正在倾听", "正在录音中，松开或结束说话...", color=0x07FF)
            recorder.record_to_wav("record.wav", button)

            if not is_sta_connected():
                print("❌ 网络断开，无法上传音频！")
                refresh_ui("网络错误", "网络连接中断，无法上传音频！", color=0xF800)
                continue

            # 步骤 2：语音识别 (ASR)
            print("🔍 正在识别语音...")
            refresh_ui("语音识别", "正在识别您的语音内容...", color=0xFFE0)
            user_text = transcribe_wav("record.wav")
            print(f"🗣️ 用户说: {user_text}")

            # 步骤 3：AI 思考与回答
            if user_text and not user_text.startswith("Error"):
                refresh_ui("AI 思考中", f"我：{user_text}\n\nAI 正在思考回答...", color=0xFFE0)
                print("🤖 正在请求 AI 大模型...")
                ai_reply = chat_ask(user_text)
                print(f"💡 AI 回答: {ai_reply}")

                # 屏幕渲染 AI 文字
                refresh_ui("AI 回复", ai_reply, color=0xFFFF)

                # 步骤 4：文本转语音 (TTS)
                if ai_reply:
                    tts_success = text_to_speech(ai_reply, filename="tts_output.wav")

                    # 步骤 5：音频播放
                    if tts_success:
                        print("🔊 正在播放语音回答...")
                        play_wav("tts_output.wav")

            else:
                refresh_ui("识别失败", "没有听清您说的话，请重试", color=0xF800)
                time.sleep(1.5)

            # 恢复待机
            refresh_ui("AI 语音助手", "待机中，长按 Boot 键开始下一次对话", color=0x07E0)
            print("\n----------------------------------")
            print("👉 等待下一次按键对话...")

    time.sleep(0.05)
