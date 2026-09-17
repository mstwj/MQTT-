# ==========================================
# 4. 连接网络 (Wi-Fi 协议栈放在后面)
# ==========================================
import gc
import time
import wifi_manager
from ai_guodong import send_bmp_to_ai
from xindisplay_ui import UIManager

# 1. 初始化 UI 管理器
ui = UIManager()

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
ai_result_bytes = send_bmp_to_ai("photo.bmp", "严格基于参考图片进行面部保留修改：保持画面中的五官、脸型、皮肤细节、背景及表情 100% 不变，仅将该人物的头发颜色染成自然红色")

# 检查返回结果并处理
if ai_result_bytes:
    print(
        f"✅ AI 处理成功！拿到图像字节流，共 {len(ai_result_bytes)} 字节"
    )
    # 此处 ai_result_bytes 已经是 320x240 的 BMP 字节流，可直接送去屏幕渲染刷新    
    ui.lcd.draw_bmp("result.bmp", start_x=0, start_y=0)        
    
else:
    print("❌ AI 请求失败，未获取到有效图像数据")