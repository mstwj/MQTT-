# app_controller.py - 硬件驱动控制与相机/UI/语音/AI 交互控制器
import gc
import time
from ai_guodong import send_bmp_to_ai
from asr_client import transcribe_wav
from audio_recorder import AudioRecorder
from machine import Pin
import wifi_manager


class AppController:

    def __init__(self, ui, cam_ctrl):
        self.ui = ui
        self.cam = cam_ctrl

        # 硬件引脚配置
        self.boot_btn = Pin(0, Pin.IN, Pin.PULL_UP)  # IO0: 拍照/开关相机
        self.view_btn = Pin(46, Pin.IN, Pin.PULL_UP)  # IO46: 浏览/退出浏览
        self.voice_btn = Pin(14, Pin.IN, Pin.PULL_UP)  # IO14: 录音/语音对话

        self.press_start_time = 0
        self.is_processing_voice = False

    def enter_view_mode(self):
        """进入浏览照片模式（仅在此模式下响应 IO14 语音对话，IO46 退出浏览）"""
        filename = "photo.bmp"
        print("🔍 进入浏览模式，读取:", filename)

        try:
            with open(filename, "rb") as f:
                f.seek(66)
                bmp_data = f.read(320 * 240 * 2)

            if not bmp_data or len(bmp_data) != 320 * 240 * 2:
                self.ui.lcd.fill(0x0000)
                self.ui.font.text(
                    self.ui.lcd,
                    "照片损坏/不完整",
                    40,
                    100,
                    color=0xF800,
                )
                self.ui.lcd.show()
                time.sleep_ms(1500)
                return

            # 显示存好的照片
            display_buf = self.cam.swap_endian(bmp_data)
            self.ui.lcd.push_camera_buf(display_buf, 320, 240)

            # 消抖：等待进入浏览模式的按键松开
            while self.view_btn.value() == 0:
                time.sleep_ms(20)

            # === 浏览模式专属独立子循环 ===
            while True:
                # 🌟 1. 【核心逻辑】仅在浏览模式下检测 IO14 触发语音对话
                if self.voice_btn.value() == 0:
                    self.handle_voice_dialog()
                    # 语音处理完后重新刷一次当前屏幕（避免 UI 遗留文字）
                    display_buf = self.cam.swap_endian(bmp_data)
                    self.ui.lcd.push_camera_buf(display_buf, 320, 240)

                # 🌟 2. 按下 IO46 退出浏览，返回实时预览
                if self.view_btn.value() == 0:
                    time.sleep_ms(20)
                    if self.view_btn.value() == 0:
                        print("🚪 退出浏览模式，返回实时画面模式")
                        while self.view_btn.value() == 0:
                            time.sleep_ms(20)
                        break

                time.sleep_ms(30)

        except OSError:
            print("⚠️ 未找到 photo.bmp！")
            self.ui.lcd.fill(0x0000)
            self.ui.font.text(
                self.ui.lcd,
                "尚未拍照无存图!",
                40,
                100,
                color=0xF800,
            )
            self.ui.lcd.show()
            time.sleep_ms(1500)

    def handle_voice_dialog(self):
        """处理 IO14 语音录制、识别与 AI 图文交互全流程"""
        if self.is_processing_voice or self.voice_btn.value() != 0:
            return

        time.sleep_ms(20)  # 消抖
        if self.voice_btn.value() != 0:
            return

        self.is_processing_voice = True

        try:
            # 1. 显示录音 UI 并录音
            self.ui.render(
                "语音对话", "🎙️ 正在录音中...\n松开按键结束"
            )
            self.ui.draw_rec_dot(True)

            recorder = AudioRecorder()
            recorder.record("record.wav", self.voice_btn, max_seconds=15)
            recorder.close()
            self.ui.draw_rec_dot(False)

            # 2. 检查网络与语音识别
            if not wifi_manager.is_sta_connected():
                self.ui.render("错误", "❌ 网络已断开，无法识别")
                time.sleep(1.5)
            else:
                self.ui.render("语音识别", "🔍 正在识别语音...")
                user_text = transcribe_wav("record.wav")

                if user_text:
                    print(f"🗣️ 用户说: {user_text}")
                    self.ui.render("识别结果", user_text)
                    time.sleep(1.5)
                    
                    user_text +="原图不变,只改动需要改动的部分"
                
                    # 3. 发送图片+文本请求 AI 处理
                    self.ui.render(
                        "AI 处理中", "🎨 AI 正在重绘图像..."
                    )
                    # 传入 ui.render 回调函数给底层，底层将自动在各个节点刷屏提示
                    ai_result_bytes = send_bmp_to_ai(
                        "photo.bmp",
                        user_text,
                        ui_callback=lambda title, msg: self.ui.render(title, msg),
                    )

                    if ai_result_bytes:
                        print(
                            f"✅ AI 处理成功！拿到图像字节流，共 {len(ai_result_bytes)} 字节"
                        )
                        # 直接读取并刷屏显示 AI 返回的 BMP
                        self.ui.lcd.draw_bmp(
                            "result.bmp", start_x=0, start_y=0
                        )
                        time.sleep(8)
                    else:
                        print("❌ AI 请求失败，未获取到有效图像数据")
                        self.ui.render("AI 错误", "❌ 图片生成失败")
                        time.sleep(1.5)
                else:
                    self.ui.render(
                        "识别提示", "⚠️ 未听清或说话时间太短"
                    )
                    time.sleep(1.5)

        except Exception as req_err:
            print(f"💥 语音流程发生捕获异常: {req_err}")
            self.ui.render("系统错误", f"{req_err}")
            time.sleep(1.5)

        finally:
            self.is_processing_voice = False
            gc.collect()

    def handle_main_loop(self):
        """主循环事件处理中心（实时画面模式）"""
        # === A. 检测是否按下 IO46 进入浏览模式 ===
        if self.view_btn.value() == 0:
            time.sleep_ms(20)
            if self.view_btn.value() == 0:
                self.enter_view_mode()
                return

        # === B. BOOT 按键 (IO0) 检测：短按拍照 / 长按开关相机 ===
        if self.boot_btn.value() == 0:
            if self.press_start_time == 0:
                self.press_start_time = time.ticks_ms()

            elif (
                time.ticks_diff(time.ticks_ms(), self.press_start_time) > 1500
            ):
                # 长按切换摄像头开关
                if self.cam.is_active:
                    self.cam.deinit_cam()
                    self.ui.lcd.fill(0x0000)
                    self.ui.font.text(
                        self.ui.lcd,
                        "摄像头已关闭",
                        60,
                        100,
                        color=0xF800,
                    )
                    self.ui.lcd.show()
                else:
                    self.cam.init_cam()

                while self.boot_btn.value() == 0:
                    time.sleep_ms(20)
                self.press_start_time = 0

        else:
            if self.press_start_time > 0:
                duration = time.ticks_diff(
                    time.ticks_ms(), self.press_start_time
                )
                self.press_start_time = 0

                # 短按拍照
                if duration < 1000:
                    if self.cam.is_active:
                        print("📸 触发拍照中...")
                        buf = self.cam.capture_frame()
                        if buf:
                            try:
                                self.ui.lcd.fill(0xFFFF)
                                self.ui.lcd.show()
                            except Exception:
                                pass
                            time.sleep_ms(50)

                            # 保存图像
                            self.cam.save_photo_bmp(buf, "photo.bmp")

                            # 画面回显并提示
                            self.ui.lcd.push_camera_buf(buf, 320, 240)
                            time.sleep_ms(500)
                    else:
                        print("⚠️ 摄像头未开启！")

        # === C. 摄像头实时推流刷新 ===
        if self.cam.is_active:
            buf = self.cam.capture_frame()
            if buf:
                self.ui.lcd.push_camera_buf(buf, 320, 240)
            time.sleep_us(500)
        else:
            time.sleep_ms(50)