import time
from machine import Pin

#语音转文字...
from asr_client import transcribe_wav

#文字AI
from ai_client import chat_ask

#图片AI
from ai_bmp_client import generate_and_download_image


from wifi_manager import (
    load_wifi_config,
    connect_router_wifi,
    start_ap_web_server,
    is_sta_connected,
)


ssid, pwd = load_wifi_config()
connect_ok = False
current_ip = None


if ssid and pwd:
    print("正在连接无线网络...")
    connect_ok, current_ip = connect_router_wifi(ssid, pwd)
    
    
    
if not connect_ok:
    print("WiFi 连接失败，启动配网模式...")    
    start_ap_web_server(refresh_ui)
    
# ==========================================
# 1. 初始化 硬件、UI 与 全局对象
# ==========================================
button = Pin(0, Pin.IN, Pin.PULL_UP)

wifi_online_last = False    


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
        else:
            print("⚠️ 网络连接中断！")            
        wifi_online_last = online

    # 监测录音按键
    if button.value() == 0:
        time.sleep_ms(20)  # 消抖
        if button.value() == 0:

            # 步骤 1：录音
            print("\n🎙️ 听到按键，开始录音...")
            if not is_sta_connected():
                print("❌ 网络断开，无法上传音频！")                
                continue

            # 步骤 2：语音识别 (ASR)
            #print("🔍 正在识别语音...")
            user_text = "给我一个"
            print(f"🗣️ 用户说: {user_text}")

            print("🤖 正在请求 AI 大模型...")
            ai_reply = chat_ask(user_text)
            print(f"💡 AI 回答: {ai_reply}")
            
            #generate_and_download_image("我要一个小猪")

            # 恢复待机
            print("\n----------------------------------")
            print("👉 等待下一次按键对话...")

    time.sleep(0.05)