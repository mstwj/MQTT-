# main.py - 综合主控入口脚本
import gc
import time
from app_controller import AppController
from camera_driver import CameraController
from xindisplay_ui import UIManager
import wifi_manager

# 1. 垃圾回收，优化系统启动内存
gc.collect()

# 2. 优先初始化摄像头（抢占 DMA 内存）
cam = CameraController()
cam.init_cam()
gc.collect()
time.sleep_ms(300)

# 3. 初始化 UI 界面
ui = UIManager()
ui.render("系统启动中...", "正在准备连接网络...")
gc.collect()
time.sleep_ms(300)

# 4. 连接网络
ssid, pwd = wifi_manager.load_wifi_config()
connect_ok = False
current_ip = None

if ssid and pwd:
    ui.render("连接 Wi-Fi", f"正在连接:\n{ssid}")
    try:
        connect_ok, current_ip = wifi_manager.connect_router_wifi(
            ssid, pwd, ui_callback=lambda title, msg: ui.render(title, msg)
        )
    except Exception as e:
        print(f"❌ Wi-Fi 连接异常: {e}")

if not connect_ok:
    ui.render(
        "热点配网模式",
        "请连接热点:\nESP32-Recorder\n访问: 192.168.4.1",
    )
    wifi_manager.start_ap_web_server(
        ui_callback=lambda title, msg: ui.render(title, msg)
    )

ui.render("网络已连接", f"IP: {current_ip}")
time.sleep(1)

# 5. 初始化应用控制器
app = AppController(ui, cam)

print("\n------------------------------------------------")
print("👉 【实时模式】短按 BOOT 键(IO0)：拍照保存")
print("👉 【实时模式】长按 BOOT 键(IO0)：开关摄像头")
print("👉 【实时模式】按下 IO46：进入浏览模式")
print("👉 【实时模式】按住 IO14：进行语音对话处理")
print("👉 【浏览模式】再次按下 IO46：退出浏览并恢复拍照")
print("------------------------------------------------\n")

# 6. 主事件循环
while True:
    try:
        app.handle_main_loop()
    except Exception as e:
        print(f"⚠️ 系统运行异常: {e}")
        time.sleep(1)

    time.sleep_ms(10)