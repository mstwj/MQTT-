# main.py - 先联网 + 摄像头 + 浏览/语音对话 综合主控程序
import gc
import time
from app_controller import AppController
from camera_driver import CameraController
from machine import Pin

# 导入网络管理与语音识别模块
import wifi_manager
from asr_client import transcribe_wav
from xindisplay_ui import UIManager

# ==========================================
# 1. 初始化显示屏 (优先加载 UI 以显示连接状态)
# ==========================================
ui = UIManager()
ui.render("系统启动中...", "正在准备连接网络...")

# ==========================================
# 2. 先连接网络 (黄金顺序：先 Wi-Fi，后摄像头)
# ==========================================
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
    # 若 Wi-Fi 连接失败或无配置，启动 AP 热点配网模式
    ui.render("热点配网模式", "请连接热点:\nESP32-Recorder\n访问: 192.168.4.1")
    wifi_manager.start_ap_web_server(
        ui_callback=lambda title, msg: ui.render(title, msg)
    )

# 网络连接成功提示
ui.render("网络已连接", f"IP: {current_ip}\n正在启动摄像头...")
time.sleep(1)

# ==========================================
# 3. 后初始化摄像头 (解决 0x0101 内存冲突)
# ==========================================
cam = CameraController()
cam.init_cam()

# ==========================================
# 4. 构建应用控制器与初始化按键
# ==========================================
app = AppController(ui, cam)

# 初始化语音对话按键 (IO14)
voice_btn = Pin(14, Pin.IN, Pin.PULL_UP)

print("\n------------------------------------------------")
print("👉 【实时模式】短按 BOOT 键(IO0)：拍照保存")
print("👉 【实时模式】长按 BOOT 键(IO0)：开关摄像头")
print("👉 【实时模式】按下 IO46：进入浏览模式")
print("👉 【浏览模式】按住 IO14：进行语音对话处理")
print("👉 【浏览模式】再次按下 IO46：退出浏览并恢复拍照")
print("------------------------------------------------\n")

# ==========================================
# 5. 主系统事件循环
# ==========================================
is_processing_voice = False

while True:
    try:
        # A. 优先轮询底层的画面刷屏与按键逻辑
        app.handle_main_loop()

        # B. 检测 IO14 语音对话按键 (在浏览模式或特定模式下触发)
        if not is_processing_voice and voice_btn.value() == 0:
            time.sleep_ms(20)  # 消抖
            if voice_btn.value() == 0:
                is_processing_voice = True

                try:
                    # 暂停实时画面刷新，显示录音 UI
                    ui.render("语音对话", "🎙️ 正在录音中...\n松开按键结束")
                    ui.draw_rec_dot(True)

                    # 调用录音 (内部会自动检测 voice_btn 松开)
                    from audio_recorder import AudioRecorder

                    recorder = AudioRecorder()
                    recorder.record("record.wav", voice_btn, max_seconds=15)
                    recorder.close()

                    ui.draw_rec_dot(False)

                    # 检查网络并上传识别
                    if not wifi_manager.is_sta_connected():
                        ui.render("错误", "❌ 网络已断开，无法识别")
                    else:
                        ui.render("语音识别", "🔍 正在识别语音...")
                        user_text = transcribe_wav("record.wav")

                        if user_text:
                            print(f"🗣️ 用户说: {user_text}")
                            ui.render("识别结果", user_text)
                            time.sleep(2)
                        else:
                            ui.render("识别提示", "⚠️ 未听清或说话时间太短")
                            time.sleep(1.5)

                except Exception as req_err:
                    print(f"💥 语音流程发生捕获异常: {req_err}")
                    ui.render("系统错误", f"{req_err}")
                    time.sleep(1.5)

                finally:
                    is_processing_voice = False
                    gc.collect()

    except Exception as e:
        print(f"⚠️ 系统运行异常: {e}")
        time.sleep(1)

    time.sleep(0.02)
