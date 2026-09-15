# esp_stream.py - 摄像头实时抓图直显（零拷贝极速推流）
import time
import camera
from xindisplay_ui import UIManager

# 1. 初始化 UI 管理器
ui = UIManager()

# 2. 初始化摄像头
try:
    camera.deinit()
    time.sleep_ms(200)
except:
    pass

camera.init(
    0,
    d0=11, d1=9, d2=8, d3=10,
    d4=12, d5=18, d6=17, d7=16,
    format=0,                        # 0 代表 RGB565 直出
    framesize=camera.FRAME_QVGA,  # 240x240 方形分辨率
    xclk_freq=20000000,    
    vsync=6, href=7, siod=4, sioc=5,
    pwdn=-1, reset=-1, xclk=15, pclk=13
)
print("🎉 摄像头初始化成功（内存直出性能测试模式）！")
time.sleep(1)

# 3. 实时循环抓图并刷屏
while True:
    try:
        # --- [1] 统计摄像头抓图耗时 ---
        t0 = time.ticks_us()
        buf = camera.capture()
        t1 = time.ticks_us()
        
        if not buf:
            time.sleep_ms(2)
            continue

        # --- [2] 零拷贝直接打入 SPI 屏幕 ---
        t2 = time.ticks_us()
        ui.lcd.push_camera_buf(buf, 320, 240) # 移除了 start_x, start_y
        # 2. 关键补全：把缓冲区图像强行刷入物理屏幕！
        #ui.lcd.show()
        
        t3 = time.ticks_us()

        # 计算各环节耗时
        cap_ms = time.ticks_diff(t1, t0) / 1000.0
        stream_ms = time.ticks_diff(t3, t2) / 1000.0
        total_ms = time.ticks_diff(t3, t0) / 1000.0

        print(f"⏱️ 抓图: {cap_ms:.2f}ms | SPI直推: {stream_ms:.2f}ms | 单帧总耗时: {total_ms:.2f}ms")
        # 错开 VSYNC 帧头，避免出现 83ms 的双倍阻塞跳动
        time.sleep_us(500)

    except Exception as err:
        print(f"⚠️ 运行异常: {err}")
        time.sleep(1)