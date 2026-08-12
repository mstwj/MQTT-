import time
from oled_driver import refresh_ui
from wifi_manager import (
    load_wifi_config,
    connect_router_wifi,
    start_ap_web_server,
    is_sta_connected,
)
from ai_client import chat_ask

# 加载WiFi配置
ssid, pwd = load_wifi_config()
connect_ok = False
current_ip = None

if ssid and pwd:
    # 英文UI提示
    connect_ok, current_ip = connect_router_wifi(ssid, pwd, refresh_ui)

# 连接失败进入AP配网（阻塞）
if not connect_ok:
    start_ap_web_server(refresh_ui)

wifi_online_last = None
ai_calling = False  # 防止重复并发调用AI

# ============ 业务主循环 ============
while True:
    online = is_sta_connected()

    # WiFi状态变化刷新屏幕（英文显示）
    if online != wifi_online_last:
        if not online:
            refresh_ui("Network", "Wi-Fi Disconnected\nReconnecting...")
        else:
            refresh_ui("Network", f"Connected\nIP:{current_ip}")
        wifi_online_last = online

    # ========== AI调用示例 ==========
    if online and not ai_calling:
        ai_calling = True
        try:
            refresh_ui("AI Status", "Requesting...\nPlease wait")

            # 发起 AI 提问
            result = chat_ask("Hello, introduce yourself briefly.")
            print("AI Result:", result)

            # OLED 显示英文回复
            # 8x8 基础字库每行可显示约 16 个英文字符，截取前 48 个字符完美填充屏幕
            refresh_ui("AI Response", result[:48])

            # 请求成功后，让 ESP32 休息一会儿，避免频繁刷接口
            time.sleep(15)

        except Exception as err:
            print("AI Exception Captured:", err)
            refresh_ui("System Error", "Request Failed\nTry again later")
            time.sleep(5)

        finally:
            # 关键！重置状态标志，防止卡死
            ai_calling = False

    time.sleep(2)