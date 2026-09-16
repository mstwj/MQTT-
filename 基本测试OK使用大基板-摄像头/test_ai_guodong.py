

# ==========================================
# 4. 连接网络 (Wi-Fi 协议栈放在后面)
# ==========================================
import gc
import time
import wifi_manager
from ai_guodong import send_bmp_to_ai

ssid, pwd = wifi_manager.load_wifi_config()
connect_ok = False
current_ip = None

if ssid and pwd:    
    try:
        connect_ok, current_ip = wifi_manager.connect_router_wifi(
            ssid, pwd, ui_callback=lambda title, msg: ui.render(title, msg)
        )
    except Exception as e:
        print(f"❌ Wi-Fi 连接异常: {e}")

if not connect_ok:
    wifi_manager.start_ap_web_server(
        ui_callback=lambda title, msg: ui.render(title, msg)
    )

# 网络连接成功提示
time.sleep(1)

# 只需要一行代码调用：
ai_result_bytes = send_bmp_to_ai("photo.bmp", "把照片的头发搞成黄色")

# 如果接收到了返回的图片字节数据，保存为新图片：
if ai_result_bytes:
    with open("ai_out.jpg", "wb") as f:
        f.write(ai_result_bytes)
    print("AI 结果图已保存为 ai_out.jpg")